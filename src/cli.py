from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.config import ROOT


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover Once, Replay Many")
    sub = parser.add_subparsers(dest="command", required=True)

    discover_p = sub.add_parser("discover", help="LLM computer-use exploration against the mock portal")
    discover_p.add_argument("--goal", required=True)
    discover_p.add_argument("--url", default=None)
    discover_p.add_argument("--headed", action="store_true")

    replay_p = sub.add_parser("replay", help="Deterministic zero-LLM replay of a capability artifact")
    replay_p.add_argument("--artifact", default=str(ROOT / "evidence" / "capability_artifact.json"))
    replay_p.add_argument("--inputs", required=True, help="JSON file of runner arguments")
    replay_p.add_argument("--log", default=None)
    replay_p.add_argument("--headed", action="store_true")
    replay_p.add_argument("--approve-risky", action="store_true", help="Allow irreversible steps without HITL")
    replay_p.add_argument("--hitl", action="store_true", help="Pause on irreversible steps and wait for resume")
    replay_p.add_argument("--hitl-auto-resume", type=float, default=None, help="Seconds to wait, then auto-resume (demo)")

    sub.add_parser("resume", help="Signal resume to a paused live session")

    args = parser.parse_args(argv)
    if args.command == "discover":
        from src.agent.loop import discover

        result = discover(args.goal, url=args.url, headed=True if args.headed else None)
        print(
            json.dumps(
                {
                    "artifact_path": result["artifact_path"],
                    "log_path": result["log_path"],
                    "artifact_id": result["artifact"]["id"],
                    "llm_calls": result["llm_calls"],
                },
                indent=2,
            )
        )
        return 0
    if args.command == "replay":
        from src.engine.replay import replay

        inputs = json.loads(Path(args.inputs).read_text(encoding="utf-8"))
        log_path = Path(args.log) if args.log else ROOT / "evidence" / "replay.log"
        result = replay(
            args.artifact,
            inputs,
            log_path=log_path,
            headed=True if args.headed else None,
            approve_risky=args.approve_risky,
            hitl=args.hitl,
            hitl_auto_resume_s=args.hitl_auto_resume,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["status"] in {"success", "business_outcome"} else 1
    if args.command == "resume":
        from src.hitl.handoff import LiveHandoff

        LiveHandoff().signal_resume("cli")
        print("Resume signaled for the live browser session.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
