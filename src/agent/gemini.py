from __future__ import annotations

import json
import re
import time
from typing import Any

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from src.agent.prompts import SYSTEM_PROMPT, observation_user_payload
from src.config import get_settings

FUNCTION_DECLARATION = types.FunctionDeclaration(
    name="computer_act",
    description="Take one computer-use action on the live UI, or finish the goal.",
    parameters={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["CLICK", "TYPE", "NAVIGATE", "WAIT_FOR", "READ", "DONE"],
            },
            "strategy": {
                "type": "string",
                "enum": ["visible_text", "nearby_label", "table_cell", "coordinates", "text_matches"],
            },
            "text": {"type": "string"},
            "label": {"type": "string"},
            "column_header": {"type": "string"},
            "row_index": {"type": "integer"},
            "pattern": {"type": "string"},
            "x": {"type": "integer"},
            "y": {"type": "integer"},
            "value": {"type": "string"},
            "url": {"type": "string"},
            "goal_complete": {"type": "boolean"},
            "outputs": {
                "type": "object",
                "properties": {
                    "confirmation_id": {"type": "string"},
                    "savings_balance": {"type": "string"},
                    "current_balance": {"type": "string"},
                },
            },
        },
        "required": ["action"],
    },
)


def _parse_json_action(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and "action" in data:
        return data
    return None


class GeminiComputerUse:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is missing. Copy .env.example to .env and set the key.")
        self.model = settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def decide(self, goal: str, step: int, observation: dict, screenshot_jpeg: bytes, last_error: str | None) -> tuple[dict[str, Any], dict[str, Any]]:
        user_text = observation_user_payload(goal, step, observation, last_error)
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=user_text),
                    types.Part.from_bytes(data=screenshot_jpeg, mime_type="image/jpeg"),
                ],
            )
        ]
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0.1,
            tools=[types.Tool(function_declarations=[FUNCTION_DECLARATION])],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode="ANY",
                    allowed_function_names=["computer_act"],
                )
            ),
        )
        api_error: Exception | None = None
        response = None
        for attempt in range(6):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=config,
                )
                break
            except (ClientError, ServerError) as exc:
                api_error = exc
                message = str(exc)
                if "429" not in message and "RESOURCE_EXHAUSTED" not in message and "503" not in message and "UNAVAILABLE" not in message:
                    raise
                delay = 20.0 * (attempt + 1)
                if "503" in message or "UNAVAILABLE" in message:
                    delay = 8.0 * (attempt + 1)
                match = re.search(r"retry in ([\d.]+)s", message, re.I)
                if match:
                    delay = float(match.group(1)) + 2
                time.sleep(delay)
        else:
            raise api_error or RuntimeError("Gemini request failed")
        assert response is not None
        usage = {
            "input_tokens": getattr(getattr(response, "usage_metadata", None), "prompt_token_count", None),
            "output_tokens": getattr(getattr(response, "usage_metadata", None), "candidates_token_count", None),
        }
        calls = getattr(response, "function_calls", None) or []
        if calls:
            args = dict(calls[0].args or {})
            return args, usage
        payload = _parse_json_action(getattr(response, "text", "") or "")
        if payload:
            return payload, usage
        raise RuntimeError("Gemini did not return a computer_act function call")
