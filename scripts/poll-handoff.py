#!/usr/bin/env python3
"""Poll the other side's handoff report for new tasks.

Cross-OS (Windows/Linux/macOS), stdlib only. Used by scheduled jobs
(opencode-scheduler, schtasks, cron, systemd) as the deterministic
check step: the agent only works when this script reports NEW items.

Usage:
    python scripts/poll-handoff.py --inbox test/linux_compat_report.md --watch NEEDS-WINDOWS
    python scripts/poll-handoff.py --inbox test/windows_compat_report.md --watch NEEDS-WINDOWS

State (already-seen item hashes) lives OUTSIDE the repo so polling
never dirties the working tree:
    Windows: %APPDATA%\\human-skills-handoff\\state.json
    POSIX:   ~/.config/human-skills-handoff/state.json

Exit codes: 0 = ok (prints NEW:... lines or NO-NEW), 1 = usage/git error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# Windows consoles default to cp1252: force UTF-8 so report lines
# with emoji/symbols never crash the poller.
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent


def state_file() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    p = base / "human-skills-handoff" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_state() -> dict:
    try:
        return json.loads(state_file().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    state_file().write_text(json.dumps(state, indent=2), encoding="utf-8")


def git_pull() -> bool:
    try:
        r = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if r.returncode != 0:
            print(f"GIT-WARN: pull failed: {r.stderr.strip()[:200]}", file=sys.stderr)
            return False
        return True
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f"GIT-WARN: pull error: {e}", file=sys.stderr)
        return False


def extract_items(inbox: Path, token: str) -> list[str]:
    if not inbox.is_file():
        print(f"NO-INBOX: {inbox} does not exist yet (other side has not reported).")
        return []
    items = []
    for line in inbox.read_text(encoding="utf-8").splitlines():
        if token in line:
            items.append(line.strip())
    return items


def main() -> int:
    ap = argparse.ArgumentParser(description="Poll handoff inbox for new tasks.")
    ap.add_argument("--inbox", required=True, help="Inbox file relative to repo root.")
    ap.add_argument("--watch", required=True, help="Token marking actionable items.")
    ap.add_argument("--no-pull", action="store_true", help="Skip git pull (offline check).")
    ap.add_argument("--mark-seen", action="store_true", help="Mark current items seen without printing NEW.")
    args = ap.parse_args()

    if not args.no_pull:
        git_pull()

    inbox = REPO_ROOT / args.inbox
    items = extract_items(inbox, args.watch)
    if not inbox.is_file():
        return 0

    key = f"{args.inbox}::{args.watch}"
    seen = set(load_state().get(key, []))
    fresh = [it for it in items if hashlib.sha256(it.encode()).hexdigest()[:16] not in seen]

    if args.mark_seen:
        state = load_state()
        state[key] = [hashlib.sha256(it.encode()).hexdigest()[:16] for it in items]
        save_state(state)
        print(f"MARKED-SEEN: {len(items)} items.")
        return 0

    if not fresh:
        print("NO-NEW: nothing actionable since last check.")
        return 0

    print(f"NEW: {len(fresh)} actionable item(s) in {args.inbox}:")
    for it in fresh:
        print(f"  - {it}")
    state = load_state()
    state[key] = [hashlib.sha256(it.encode()).hexdigest()[:16] for it in items]
    save_state(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
