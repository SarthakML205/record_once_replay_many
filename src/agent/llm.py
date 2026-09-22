from __future__ import annotations

import json
from typing import Any, Protocol

from src.config import get_settings


class DecisionModel(Protocol):
    provider: str
    model_name: str

    def decide(
        self,
        goal: str,
        step: int,
        observation: dict,
        screenshot_jpeg: bytes | None,
        last_error: str | None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        ...


def get_decision_model() -> DecisionModel:
    settings = get_settings()
    if settings.llm_provider == "ollama":
        from src.agent.ollama_client import OllamaComputerUse

        return OllamaComputerUse()
    from src.agent.gemini import GeminiComputerUse

    return GeminiComputerUse()
