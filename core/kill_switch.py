"""Global kill switch — 08_GOVERNANCE_AND_SAFETY.md.

The Chairperson must always have a single command that immediately halts all
autonomous execution across every department, independent of any department's
state. Implemented as a flag file: no database, no network, no dependency that
could itself be down. Every agent action must call `guard()` first.

CLI:
    python -m core.kill_switch pause   [reason]
    python -m core.kill_switch resume
    python -m core.kill_switch status
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_PAUSE_FILE = Path(__file__).resolve().parent.parent / "data" / "GLOBAL_PAUSE"


def pause_file() -> Path:
    """Resolvable at call time so tests/deployments can relocate it (AE_OS_PAUSE_FILE)."""
    override = os.environ.get("AE_OS_PAUSE_FILE")
    return Path(override) if override else DEFAULT_PAUSE_FILE


class SystemPaused(Exception):
    """Raised when any agent attempts to act while the kill switch is engaged."""


def _read() -> dict:
    f = pause_file()
    if not f.exists():
        return {"paused": False}
    try:
        return json.loads(f.read_text())
    except (json.JSONDecodeError, OSError):
        # Unreadable/corrupt flag file fails SAFE: treat as paused.
        return {"paused": True, "reason": "unreadable pause file — failing safe"}


def _write(state: dict) -> None:
    f = pause_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(state, indent=2))


def is_paused() -> bool:
    return bool(_read().get("paused"))


def pause(reason: str = "Chairperson-initiated global pause") -> None:
    _write({
        "paused": True,
        "paused_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
    })


def resume() -> None:
    _write({
        "paused": False,
        "resumed_at": datetime.now(timezone.utc).isoformat(),
    })


def status() -> dict:
    return _read()


def guard() -> None:
    """Call at the top of every agent action. Raises SystemPaused if engaged."""
    if is_paused():
        info = status()
        raise SystemPaused(
            f"Global pause engaged at {info.get('paused_at', '?')}: "
            f"{info.get('reason', 'no reason recorded')}"
        )


def _cli() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "pause":
        reason = " ".join(sys.argv[2:]) or "Chairperson-initiated global pause"
        pause(reason)
        print("PAUSED —", reason)
    elif cmd == "resume":
        resume()
        print("RESUMED — autonomous execution re-enabled")
    elif cmd == "status":
        print(json.dumps(status(), indent=2))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
