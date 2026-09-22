from __future__ import annotations

import re
from typing import Any

from src.guardrails.policy import classify_action
from src.schemas.artifact import (
    ActionStep,
    CapabilityArtifact,
    Checkpoint,
    FieldSpec,
    Locator,
    OutcomeRule,
)

LABEL_TO_PARAM = {
    "Member ID": ("member_id", "string", "Core member identifier for inquiry"),
    "Account Name": ("account_name", "string", "Name of the high-yield savings sub-account"),
    "Initial Deposit": ("initial_deposit", "number", "Opening deposit for the sub-account"),
}

DEFAULT_OUTCOMES = [
    OutcomeRule(code="MEMBER_NOT_FOUND", when_text="No matching member found", outcome_class="BUSINESS"),
    OutcomeRule(code="RECORD_NOT_FOUND", when_text="Record Not Found", outcome_class="BUSINESS"),
    OutcomeRule(code="ACCOUNT_RESTRICTED", when_text="Permission denied: account is restricted", outcome_class="BUSINESS"),
    OutcomeRule(code="ACCOUNT_FROZEN", when_text="Account Frozen", outcome_class="BUSINESS"),
    OutcomeRule(code="ACCOUNT_ALREADY_FROZEN", when_text="Account already frozen", outcome_class="BUSINESS"),
    OutcomeRule(code="SUBACCOUNT_EXISTS", when_text="Sub-account already exists", outcome_class="BUSINESS"),
    OutcomeRule(code="VALIDATION_ACCOUNT_NAME", when_text="Account name is required", outcome_class="BUSINESS"),
    OutcomeRule(code="VALIDATION_DEPOSIT", when_text="Initial deposit must be a number greater than 0", outcome_class="BUSINESS"),
    OutcomeRule(code="SUCCESS_RECEIPT", when_text="Transaction complete", outcome_class="SUCCESS"),
]


def _param_ref(label: str) -> str | None:
    spec = LABEL_TO_PARAM.get(label or "")
    if not spec:
        return None
    return f"${{input.{spec[0]}}}"


def compile_artifact(goal: str, start_url: str, trajectory: list[dict[str, Any]], final_text: str) -> CapabilityArtifact:
    input_contract: dict[str, FieldSpec] = {}
    steps: list[ActionStep] = []
    saw_freeze = False
    saw_savings = False
    step_index = 0

    for event in trajectory:
        action = event["action"]
        if action == "DONE":
            continue
        locator: Locator | None = event.get("locator")
        value = event.get("value")
        if action == "TYPE" and locator and locator.label in LABEL_TO_PARAM:
            name, typ, desc = LABEL_TO_PARAM[locator.label]
            input_contract[name] = FieldSpec(type=typ, required=True, description=desc)
            value = _param_ref(locator.label)
        if locator and locator.strategy == "visible_text" and locator.text and "," in locator.text:
            locator = Locator(strategy="table_cell", column_header="Name", row_index=0)
        if locator and locator.text == "Freeze Account":
            saw_freeze = True
        if locator and locator.text == "Submit Request":
            saw_savings = True
        risk, reversibility = classify_action(action, locator)
        step_index += 1
        steps.append(
            ActionStep(
                id=f"s{step_index:02d}",
                action=action,
                risk=risk,
                reversibility=reversibility,
                locator=locator,
                value=value,
                url="${input.target_url}" if action == "NAVIGATE" else event.get("url"),
                notes="",
            )
        )

    if not any(step.action == "NAVIGATE" for step in steps):
        nav = ActionStep(
            id="s00",
            action="NAVIGATE",
            risk="SAFE",
            reversibility="REVERSIBLE",
            url="${input.target_url}",
            notes="Open the allowlisted mock portal",
        )
        steps.insert(0, nav)
        input_contract.setdefault(
            "target_url",
            FieldSpec(type="string", required=True, description="Entry URL for the mock core console"),
        )
    else:
        input_contract.setdefault(
            "target_url",
            FieldSpec(type="string", required=True, description="Entry URL for the mock core console"),
        )

    output_contract: dict[str, FieldSpec] = {}
    checkpoints = [
        Checkpoint(id="cp_app_shell", kind="text_contains", text="CoreServ Member Console"),
    ]
    if re.search(r"Confirmation ID\s+\S+", final_text):
        output_contract["confirmation_id"] = FieldSpec(
            type="string",
            required=True,
            description="Receipt identifier shown after a confirmed service action",
        )
        checkpoints.append(
            Checkpoint(
                id="cp_receipt",
                kind="text_matches",
                pattern=r"Confirmation ID\s+CNF-[A-Z0-9-]+",
            )
        )
        steps.append(
            ActionStep(
                id=f"s{len(steps)+1:02d}",
                action="READ",
                risk="SAFE",
                reversibility="REVERSIBLE",
                locator=Locator(strategy="text_matches", pattern=r"Confirmation ID\s+(CNF-[A-Z0-9-]+)"),
                extract_as="confirmation_id",
                notes="Extract receipt id; do not persist surrounding member PII",
            )
        )
    if "High-yield savings sub-account opened" in final_text or "Savings balance" in final_text:
        output_contract["savings_balance"] = FieldSpec(
            type="string",
            required=False,
            description="High-yield savings balance shown on the receipt or servicing panel",
        )

    if saw_freeze:
        name = "freeze_member_account"
        description = "Look up a member and freeze the account after explicit confirmation."
    elif saw_savings:
        name = "open_high_yield_savings"
        description = "Look up a member and open a high-yield savings sub-account after explicit confirmation."
    else:
        name = "lookup_member"
        description = "Look up a member by id and read account status fields."
        output_contract.setdefault(
            "current_balance",
            FieldSpec(type="string", required=False, description="Current balance shown in inquiry results"),
        )

    for index, step in enumerate(steps, start=1):
        step.id = f"s{index:02d}"

    return CapabilityArtifact(
        id=f"cap.{name}",
        name=name,
        description=description,
        target={
            "surface": "web",
            "entry_url_param": "target_url",
            "route_pattern": "/",
            "default_entry_url": start_url,
        },
        input_contract=input_contract,
        output_contract=output_contract,
        steps=steps,
        checkpoints=checkpoints,
        outcome_taxonomy=DEFAULT_OUTCOMES,
    )
