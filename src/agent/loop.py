from __future__ import annotations

import json
import re
from typing import Any

from src.agent.compile import compile_artifact
from src.agent.gemini import GeminiComputerUse
from src.agent.logging_util import append_jsonl
from src.agent.normalize import locator_from_tool
from src.computer_use.session import launch_session
from src.config import ROOT, get_settings
from src.guardrails.policy import GuardrailViolation, assert_action_allowed
from src.guardrails.redact import redact_obj, redact_text
from src.schemas.artifact import Locator

import time


def _public_observation(observation: dict) -> dict:
    return {
        "url": observation.get("url"),
        "title": observation.get("title"),
        "text": redact_text(observation.get("text") or ""),
        "inputs": redact_obj(
            [
                {"label": item.get("label"), "value": item.get("value"), "x": item.get("x"), "y": item.get("y")}
                for item in observation.get("inputs") or []
            ]
        ),
        "clickables": redact_obj(observation.get("clickables") or []),
    }


def _defaults_from_goal(goal: str) -> dict[str, str]:
    defaults: dict[str, str] = {}
    member = re.search(r"\bM\d+\b", goal)
    if member:
        defaults["Member ID"] = member.group(0)
    deposit = re.search(r"Initial Deposit (\d+(?:\.\d+)?)", goal, re.I)
    if deposit:
        defaults["Initial Deposit"] = deposit.group(1)
    named = re.search(r"named ([A-Za-z0-9 ]+?) with", goal, re.I)
    if named:
        defaults["Account Name"] = named.group(1).strip()
    return defaults


def _recover_payload(payload: dict, observation: dict) -> dict:
    text = observation.get("text") or ""
    clickables = [item.get("text") for item in observation.get("clickables") or []]
    inputs = {item.get("label"): (item.get("value") or "") for item in observation.get("inputs") or []}
    if "Confirmation ID" in text or "Transaction complete" in text:
        return {"action": "DONE", "goal_complete": True, "outputs": {}}
    if "Confirm" in clickables or "Confirm irreversible action" in text:
        if not (payload.get("action") == "CLICK" and (payload.get("text") == "Confirm" or payload.get("label") == "Confirm")):
            return {"action": "CLICK", "strategy": "visible_text", "text": "Confirm"}
    if inputs.get("Account Name") and inputs.get("Initial Deposit"):
        if payload.get("action") == "TYPE":
            return {"action": "CLICK", "strategy": "visible_text", "text": "Submit Request"}
    return payload


def discover(goal: str, *, url: str | None = None, headed: bool | None = None) -> dict[str, Any]:
    settings = get_settings()
    start_url = url or settings.target_app_url
    headless = settings.headless if headed is None else not headed
    evidence = ROOT / "evidence"
    log_path = evidence / "discovery_run.log"
    if log_path.exists():
        log_path.unlink()

    model = GeminiComputerUse()
    defaults = _defaults_from_goal(goal)
    trajectory: list[dict[str, Any]] = []
    deadline = time.monotonic() + settings.discovery_timeout_s
    last_error = None
    outputs: dict[str, str] = {}
    llm_calls = 0

    with launch_session(start_url, headless=headless) as session:
        for step in range(1, settings.max_steps + 1):
            if time.monotonic() > deadline:
                raise TimeoutError("Discovery exceeded DISCOVERY_TIMEOUT_S")
            time.sleep(1)
            raw = session.observe()
            public = _public_observation(raw)
            payload, usage = model.decide(goal, step, public, raw["screenshot_jpeg"], last_error)
            llm_calls += 1
            recovered = _recover_payload(payload, raw)
            overridden = recovered is not payload and recovered != payload
            payload = recovered
            action = payload.get("action")
            append_jsonl(
                log_path,
                {
                    "step": step,
                    "provider": "gemini",
                    "model": settings.gemini_model,
                    "action": action,
                    "locator": {k: payload.get(k) for k in ("strategy", "text", "label", "column_header", "row_index")},
                    "overridden": overridden,
                    "usage": usage,
                    "llm_calls": llm_calls,
                },
            )
            if action == "DONE" or payload.get("goal_complete"):
                outputs = {
                    k: str(v)
                    for k, v in (payload.get("outputs") or {}).items()
                    if k in {"confirmation_id", "savings_balance", "current_balance"}
                }
                trajectory.append({"action": "DONE", "locator": None, "value": None})
                break
            locator: Locator | None = locator_from_tool(payload, raw)
            value = payload.get("value")
            if action == "TYPE" and not value:
                value = payload.get("text")
            if action == "TYPE" and not value and locator and locator.label:
                value = defaults.get(locator.label)
            nav_url = payload.get("url")
            try:
                assert_action_allowed(action, url=nav_url, current_url=session.url, locator=locator, value=value)
                result = session.act(action, locator=locator, value=value, url=nav_url)
                last_error = None
            except (GuardrailViolation, Exception) as exc:
                last_error = str(exc)
                append_jsonl(log_path, {"step": step, "blocked_or_failed": last_error})
                continue
            trajectory.append(
                {
                    "action": action,
                    "locator": locator,
                    "value": value,
                    "url": nav_url,
                    "result": result,
                }
            )
            recent = trajectory[-3:]
            if (
                len(recent) == 3
                and all(item["action"] == "TYPE" for item in recent)
                and len({(item.get("locator") and item["locator"].label) for item in recent}) == 1
            ):
                last_error = "That field is already filled. Click Submit Request or Confirm to proceed."

        else:
            final_preview = session.page.inner_text("body")
            if "Confirmation ID" in final_preview or "Transaction complete" in final_preview:
                trajectory.append({"action": "DONE", "locator": None, "value": None})
            else:
                raise RuntimeError("Discovery hit MAX_STEPS without DONE")

        final_obs = _public_observation(session.observe())
        final_text = final_obs["text"]
        (evidence / "discovery_final.jpg").write_bytes(session.page.screenshot(type="jpeg", quality=40))

    artifact = compile_artifact(goal, start_url, trajectory, final_text)
    artifact_path = evidence / "capability_artifact.json"
    artifact_path.write_text(artifact.to_clean_json() + "\n", encoding="utf-8")
    append_jsonl(
        log_path,
        {
            "event": "compiled_artifact",
            "artifact_id": artifact.id,
            "steps": len(artifact.steps),
            "inputs": list(artifact.input_contract.keys()),
            "outputs_keys": list(artifact.output_contract.keys()),
            "extracted_outputs": redact_obj(outputs),
            "llm_calls": llm_calls,
        },
    )
    return {
        "artifact_path": str(artifact_path),
        "log_path": str(log_path),
        "artifact": json.loads(artifact.to_clean_json()),
        "outputs": outputs,
        "llm_calls": llm_calls,
    }
