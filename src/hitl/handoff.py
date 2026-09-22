from __future__ import annotations

import json
import time
from pathlib import Path

from src.config import ROOT
from src.guardrails.redact import redact_obj


class LiveHandoff:
    """Pause the current browser session, wait for an operator resume signal, then continue."""

    def __init__(self, evidence_dir: Path | None = None) -> None:
        self.evidence_dir = evidence_dir or (ROOT / "evidence")
        self.incident_path = self.evidence_dir / "hitl_incident.json"
        self.resume_path = self.evidence_dir / "hitl_resume.flag"

    def request(self, packet: dict, screenshot: bytes | None = None) -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        if screenshot:
            shot = self.evidence_dir / "hitl_pause.jpg"
            shot.write_bytes(screenshot)
            packet = {**packet, "screenshot": str(shot)}
        self.incident_path.write_text(json.dumps(redact_obj(packet), indent=2), encoding="utf-8")
        if self.resume_path.exists():
            self.resume_path.unlink()

    def signal_resume(self, note: str = "operator") -> None:
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.resume_path.write_text(note, encoding="utf-8")

    def wait(self, *, timeout_s: float = 300, auto_resume_s: float | None = None) -> str:
        if auto_resume_s is not None:
            time.sleep(auto_resume_s)
            self.signal_resume("auto-resume")
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.resume_path.exists():
                note = self.resume_path.read_text(encoding="utf-8")
                self.resume_path.unlink()
                return note.strip() or "resume"
            time.sleep(0.2)
        raise TimeoutError("HITL resume was not signaled; browser session is still open until this process exits")
