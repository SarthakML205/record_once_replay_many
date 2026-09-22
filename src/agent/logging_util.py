from __future__ import annotations

import json
from typing import Any

from src.guardrails.redact import redact_obj


def append_jsonl(path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(redact_obj(event), ensure_ascii=True) + "\n")
