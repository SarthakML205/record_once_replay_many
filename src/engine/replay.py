from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.agent.logging_util import append_jsonl
from src.computer_use.session import launch_session
from src.config import ROOT, get_settings
from src.engine.substitute import classify_text, substitute
from src.guardrails.policy import GuardrailViolation, assert_action_allowed
from src.guardrails.redact import redact_text
from src.hitl.handoff import LiveHandoff
from src.schemas.artifact import CapabilityArtifact, Checkpoint


def _check(checkpoint: Checkpoint, text: str, url: str) -> bool:
    if checkpoint.kind == "text_contains":
        return (checkpoint.text or "") in text
    if checkpoint.kind == "text_matches":
        return re.search(checkpoint.pattern or "", text) is not None
    if checkpoint.kind == "url_matches":
        return re.search(checkpoint.url_pattern or "", url) is not None
    return False


def _extract(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    if not match:
        return None
    if match.lastindex:
        return match.group(1)
    return match.group(0)


def replay(
    artifact: CapabilityArtifact | str | Path,
    inputs: dict[str, Any],
    *,
    log_path: Path | None = None,
    headed: bool | None = None,
    approve_risky: bool = False,
    hitl: bool = False,
    hitl_auto_resume_s: float | None = None,
) -> dict[str, Any]:
    if not isinstance(artifact, CapabilityArtifact):
        artifact = CapabilityArtifact.model_validate_json(Path(artifact).read_text(encoding="utf-8"))
    settings = get_settings()
    if "target_url" not in inputs:
        inputs = {**inputs, "target_url": artifact.target.get("default_entry_url") or settings.target_app_url}
    headless = settings.headless if headed is None else not headed
    log_path = log_path or (ROOT / "evidence" / "replay.log")
    if log_path.exists():
        log_path.unlink()
    handoff = LiveHandoff()
    outputs: dict[str, str] = {}
    start_url = str(inputs["target_url"])

    append_jsonl(
        log_path,
        {
            "event": "replay_start",
            "artifact_id": artifact.id,
            "llm_calls": 0,
            "input_keys": sorted(inputs.keys()),
        },
    )

    with launch_session(start_url, headless=headless) as session:
        for step in artifact.steps:
            if step.action == "DONE":
                continue
            locator = step.locator
            value = substitute(step.value, inputs)
            url = substitute(step.url, inputs)
            try:
                assert_action_allowed(step.action, url=url, current_url=session.url, locator=locator, value=value)
            except GuardrailViolation as exc:
                result = {
                    "status": "hard_failure",
                    "code": "ALLOWLIST_VIOLATION",
                    "step_id": step.id,
                    "expected": "allowlisted action",
                    "observed": str(exc),
                    "outputs": outputs,
                    "llm_calls": 0,
                }
                append_jsonl(log_path, result)
                return result

            if step.reversibility == "IRREVERSIBLE" and not approve_risky:
                if not hitl:
                    result = {
                        "status": "hard_failure",
                        "code": "RISKY_ACTION_BLOCKED",
                        "step_id": step.id,
                        "expected": "HITL resume or --approve-risky",
                        "observed": f"{step.action} {getattr(locator, 'text', None)} is irreversible",
                        "outputs": outputs,
                        "llm_calls": 0,
                    }
                    append_jsonl(log_path, result)
                    return result
                packet = {
                    "capability_id": artifact.id,
                    "step_id": step.id,
                    "reason": "IRREVERSIBLE_ACTION",
                    "action": step.action,
                    "locator": locator.model_dump(exclude_none=True) if locator else None,
                    "resume": "python -m src resume",
                }
                handoff.request(packet, session.page.screenshot(type="jpeg", quality=40))
                append_jsonl(log_path, {"event": "hitl_pause", "control": "human", "step_id": step.id})
                note = handoff.wait(auto_resume_s=hitl_auto_resume_s)
                append_jsonl(log_path, {"event": "hitl_resume", "control": "automation", "note": note, "step_id": step.id})

            try:
                raw_result = session.act(step.action, locator=locator, value=value, url=url)
            except Exception as exc:
                observed = redact_text(session.page.inner_text("body"))
                result = {
                    "status": "hard_failure",
                    "code": "STEP_FAILED",
                    "step_id": step.id,
                    "expected": f"{step.action} {locator.model_dump(exclude_none=True) if locator else ''}",
                    "observed": observed[:1500],
                    "error": str(exc),
                    "outputs": outputs,
                    "llm_calls": 0,
                }
                append_jsonl(log_path, result)
                return result

            page_text = session.page.inner_text("body")
            if step.action == "READ" and step.extract_as and locator and locator.pattern:
                extracted = _extract(page_text, locator.pattern)
                if extracted:
                    outputs[step.extract_as] = extracted

            rule = classify_text(page_text, artifact.outcome_taxonomy)
            append_jsonl(
                log_path,
                {
                    "event": "step",
                    "step_id": step.id,
                    "action": step.action,
                    "risk": step.risk,
                    "reversibility": step.reversibility,
                    "result": raw_result,
                    "outcome_hint": rule.code if rule else None,
                    "llm_calls": 0,
                },
            )
            if rule and rule.outcome_class == "BUSINESS":
                result = {
                    "status": "business_outcome",
                    "code": rule.code,
                    "step_id": step.id,
                    "outputs": outputs,
                    "llm_calls": 0,
                }
                append_jsonl(log_path, result)
                return result

        final_text = session.page.inner_text("body")
        for checkpoint in artifact.checkpoints:
            if checkpoint.optional:
                continue
            if not _check(checkpoint, final_text, session.url):
                result = {
                    "status": "hard_failure",
                    "code": "CHECKPOINT_FAILED",
                    "step_id": checkpoint.id,
                    "expected": checkpoint.model_dump(exclude_none=True),
                    "observed": redact_text(final_text)[:1500],
                    "outputs": outputs,
                    "llm_calls": 0,
                }
                append_jsonl(log_path, result)
                return result

        success_rule = classify_text(final_text, artifact.outcome_taxonomy)
        result = {
            "status": "success",
            "code": success_rule.code if success_rule else "SUCCESS",
            "outputs": outputs,
            "llm_calls": 0,
        }
        append_jsonl(log_path, result)
        return result
