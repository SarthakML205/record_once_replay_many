from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    target_app_url: str
    headless: bool
    max_steps: int
    discovery_timeout_s: int


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-flash-latest").strip(),
        target_app_url=os.getenv("TARGET_APP_URL", "http://localhost:5173").strip(),
        headless=_bool("HEADLESS", True),
        max_steps=int(os.getenv("MAX_STEPS", "30")),
        discovery_timeout_s=int(os.getenv("DISCOVERY_TIMEOUT_S", "420")),
    )
