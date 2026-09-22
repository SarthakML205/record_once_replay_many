from __future__ import annotations

import re
from typing import Any


REF = re.compile(r"\$\{input\.([a-zA-Z0-9_]+)\}")


def substitute(template: str | None, inputs: dict[str, Any]) -> str | None:
    if template is None:
        return None

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in inputs:
            raise KeyError(f"Missing input parameter {key}")
        return str(inputs[key])

    return REF.sub(repl, template)


def classify_text(text: str, taxonomy: list) -> Any | None:
    for rule in taxonomy:
        if rule.when_text and rule.when_text in text:
            return rule
    return None
