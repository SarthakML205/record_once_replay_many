from __future__ import annotations

import json
import re
from typing import Any

SSN_FULL = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SSN_LAST4 = re.compile(r"(\*{3}-\*{2}-)\d{4}")
CARD = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PERSON_NAME = re.compile(r"\b[A-Z][a-z]+,\s+[A-Z][a-z]+\b")
CONFIRMATION = re.compile(r"\bCNF-[A-Z0-9-]+\b")
MEMBER_ID = re.compile(r"\bM\d{5}\b")


def redact_text(text: str, *, mask_member_ids: bool = False) -> str:
    if not text:
        return text
    out = SSN_FULL.sub("***-**-****", text)
    out = SSN_LAST4.sub(r"\1XXXX", out)
    out = CARD.sub("[REDACTED_PAN]", out)
    out = EMAIL.sub("[REDACTED_EMAIL]", out)
    out = PERSON_NAME.sub("[REDACTED_NAME]", out)
    if mask_member_ids:
        out = MEMBER_ID.sub("[REDACTED_MEMBER_ID]", out)
    return out


def redact_obj(value: Any, *, mask_member_ids: bool = False) -> Any:
    if isinstance(value, str):
        return redact_text(value, mask_member_ids=mask_member_ids)
    if isinstance(value, list):
        return [redact_obj(item, mask_member_ids=mask_member_ids) for item in value]
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_l = str(key).lower()
            if any(
                key_l == part or key_l.endswith("_secret") or key_l.endswith("_password")
                for part in ("ssn", "password", "secret", "pan", "card", "cvv", "access_token", "api_key")
            ):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_obj(item, mask_member_ids=mask_member_ids)
        return redacted
    return value


def dumps_redacted(value: Any, *, mask_member_ids: bool = False) -> str:
    return json.dumps(redact_obj(value, mask_member_ids=mask_member_ids), indent=2)


def strip_runtime_outputs(text: str) -> str:
    return CONFIRMATION.sub("${output.confirmation_id}", text)
