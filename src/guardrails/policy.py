from __future__ import annotations

import re

from src.schemas.artifact import Locator, Reversibility, RiskLevel

ALLOWED_ACTIONS = frozenset({"CLICK", "TYPE", "NAVIGATE", "WAIT_FOR", "READ", "DONE"})

ALLOWED_TYPE_LABELS = frozenset({"Member ID", "Account Name", "Initial Deposit"})

CHROME_CLICK_TEXTS = frozenset(
    {
        "Search",
        "Submit Request",
        "Freeze Account",
        "Confirm",
        "Cancel",
        "Return to Inquiry",
    }
)

IRREVERSIBLE_CLICK_TEXTS = frozenset({"Submit Request", "Freeze Account", "Confirm"})

DEFAULT_URL_ALLOWLIST = (r"^https?://(localhost|127\.0\.0\.1):5173(/.*)?$",)

SENSITIVE_LABELS = frozenset({"ssn", "social", "password", "pin", "card", "cvv", "token", "secret"})


def url_allowed(url: str, patterns: tuple[str, ...] = DEFAULT_URL_ALLOWLIST) -> bool:
    return any(re.search(pattern, url) for pattern in patterns)


def classify_action(action: str, locator: Locator | None) -> tuple[RiskLevel, Reversibility]:
    if action in {"WAIT_FOR", "READ", "DONE", "NAVIGATE"}:
        return "SAFE", "REVERSIBLE"
    if action == "TYPE":
        return "SAFE", "REVERSIBLE"
    click_text = (locator.text if locator else None) or ""
    if click_text in IRREVERSIBLE_CLICK_TEXTS:
        return "RISKY", "IRREVERSIBLE"
    return "SAFE", "REVERSIBLE"


class GuardrailViolation(Exception):
    pass


def assert_action_allowed(
    action: str,
    *,
    url: str | None = None,
    current_url: str,
    locator: Locator | None = None,
    value: str | None = None,
) -> None:
    if action not in ALLOWED_ACTIONS:
        raise GuardrailViolation(f"Action {action} is not on the allowlist")
    if action == "NAVIGATE":
        target = url or ""
        if not url_allowed(target):
            raise GuardrailViolation(f"Navigation blocked by URL allowlist: {target}")
        return
    if not url_allowed(current_url):
        raise GuardrailViolation(f"Current page is outside the allowlist: {current_url}")
    if action == "TYPE":
        label = (locator.label if locator else None) or ""
        if label.lower() in SENSITIVE_LABELS or any(part in label.lower() for part in SENSITIVE_LABELS):
            raise GuardrailViolation(f"Typing into sensitive field is blocked: {label}")
        if locator and locator.strategy == "nearby_label" and label not in ALLOWED_TYPE_LABELS:
            raise GuardrailViolation(f"Typing is only allowed into labeled inquiry/service fields, not {label!r}")
    if action == "CLICK" and locator and locator.strategy == "visible_text":
        text = locator.text or ""
        if text and text not in CHROME_CLICK_TEXTS and locator.strategy == "visible_text":
            # Member-row clicks must be rewritten to table_cell before this check.
            if "," in text:
                raise GuardrailViolation("Clicking a personal name is blocked; use the results table cell locator")
