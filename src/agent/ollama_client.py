from __future__ import annotations

from typing import Any

import httpx

from src.agent.gemini import _parse_json_action
from src.agent.prompts import SYSTEM_PROMPT, observation_user_payload
from src.config import get_settings

TOOL = {
    "type": "function",
    "function": {
        "name": "computer_act",
        "description": "Take one computer-use action on the live UI, or finish.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["CLICK", "TYPE", "NAVIGATE", "WAIT_FOR", "READ", "DONE"],
                },
                "strategy": {"type": "string"},
                "text": {"type": "string"},
                "label": {"type": "string"},
                "column_header": {"type": "string"},
                "row_index": {"type": "integer"},
                "value": {"type": "string"},
                "url": {"type": "string"},
                "goal_complete": {"type": "boolean"},
            },
            "required": ["action"],
        },
    },
}


class OllamaComputerUse:
    provider = "ollama"

    def __init__(self) -> None:
        settings = get_settings()
        self.model_name = settings.ollama_model
        self.base = settings.ollama_base_url
        self._client = httpx.Client(timeout=120.0)

    def decide(
        self,
        goal: str,
        step: int,
        observation: dict,
        screenshot_jpeg: bytes | None,
        last_error: str | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        user_text = observation_user_payload(goal, step, observation, last_error)
        if screenshot_jpeg:
            user_text += "\n(Screenshot omitted from local text-only path; use the text observation.)"
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1},
        }
        response = self._client.post(f"{self.base}/api/chat", json=payload)
        response.raise_for_status()
        body = response.json()
        content = ((body.get("message") or {}).get("content") or "")
        parsed = _parse_json_action(content)
        if not parsed:
            raise RuntimeError(f"Ollama did not return computer_act JSON: {content[:400]}")
        usage = {
            "input_tokens": body.get("prompt_eval_count"),
            "output_tokens": body.get("eval_count"),
        }
        return parsed, usage
