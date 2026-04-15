#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              Human Skills — Automated Upstream Sync                        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Reads three config files from scripts/helpers/:                           ║
║    • upstream.yaml     — repos to git pull from                            ║
║    • path_forward.yaml — skills to copy into local skills/                 ║
║    • automation.yaml   — schedule, git, and logging settings               ║
║                                                                            ║
║  Run inside a screen session:                                              ║
║    screen -S human-skills-sync                                             ║
║    python3 scripts/sync.py                                                 ║
║    Ctrl+A, D   (detach)                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import schedule
import yaml

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR          = Path(__file__).parent.resolve()
HELPERS_DIR         = SCRIPT_DIR / "helpers"
REPO_ROOT           = SCRIPT_DIR.parent
LOGS_DIR            = SCRIPT_DIR / "logs"

UPSTREAM_CONFIG     = HELPERS_DIR / "upstream.yaml"
PATH_FORWARD_CONFIG = HELPERS_DIR / "path_forward.yaml"
AUTOMATION_CONFIG   = HELPERS_DIR / "automation.yaml"


# ── Config Loader ──────────────────────────────────────────────────────────────
def load_yaml(path: Path) -> dict:
    """Load and return a YAML file. Exits with error if file not found."""
    if not path.exists():
        print(f"[ERROR] Config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


# ── Logging Setup ──────────────────────────────────────────────────────────────
def setup_logging(level: str, log_file: Path) -> logging.Logger:
    """Configure console + file logging."""
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("human-skills")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger


# ── Git Helpers ────────────────────────────────────────────────────────────────
def run_git(args: list[str], cwd: Path, logger: logging.Logger) -> tuple[bool, str]:
    """Run a git command. Returns (success, stdout/stderr text)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, result.stderr.strip() or result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 120s"
    except Exception as exc:
        return False, str(exc)


def has_working_tree_changes(repo: Path, logger: logging.Logger) -> bool:
    """Return True if the repo has staged or unstaged changes."""
    ok, output = run_git(["status", "--porcelain"], repo, logger)
    return ok and bool(output.strip())


# ── Core Steps ─────────────────────────────────────────────────────────────────
def pull_upstreams(upstreams: list[dict], logger: logging.Logger) -> dict[str, bool]:
    """
    Run `git pull` in every upstream repo.
    Returns {name: success_bool}.
    """
    results: dict[str, bool] = {}

    for entry in upstreams:
        name = entry.get("name", "unnamed")
        path = Path(entry.get("path", ""))

        if not path.exists():
            logger.warning(f"  ⚠  [{name}] path not found — skipping: {path}")
            results[name] = False
            continue

        logger.info(f"  ↓  Pulling [{name}] …")
        ok, output = run_git(["pull"], cwd=path, logger=logger)

        if ok:
            tag = "already up to date" if "Already up to date" in output else output or "updated"
            logger.info(f"     ✓  {tag}")
            results[name] = True
        else:
            logger.error(f"     ✗  {output}")
            results[name] = False

    return results


def forward_skills(forwards: list[dict], logger: logging.Logger) -> list[str]:
    """
    Copy skill folders from upstream paths → local skills/.
    Destination is fully overwritten on every run.
    Returns list of skill names that were successfully copied.
    """
    copied: list[str] = []

    for rule in forwards:
        if not rule.get("enabled", True):
            logger.debug(f"  –  Skipping disabled rule: {rule.get('from', '?')}")
            continue

        src = Path(rule.get("from", ""))
        dst = Path(rule.get("to", ""))
        skill_name = src.name

        if not src.exists():
            logger.warning(f"  ⚠  Source not found — skipping: {src}")
            continue

        logger.info(f"  →  Forwarding [{skill_name}] …")
        try:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            logger.info(f"     ✓  {src} → {dst}")
            copied.append(skill_name)
        except Exception as exc:
            logger.error(f"     ✗  Copy failed: {exc}")

    return copied


def push_repo(
    repo: Path,
    commit_msg: str,
    branch: str,
    logger: logging.Logger,
) -> bool:
    """
    Stage all changes, commit, and push to origin/<branch>.
    Skips silently if there are no changes.
    """
    if not has_working_tree_changes(repo, logger):
        logger.info("  ✓  Nothing to commit — repo is clean.")
        return True

    logger.info("  📦 Staging all changes …")
    ok, out = run_git(["add", "."], repo, logger)
    if not ok:
        logger.error(f"     ✗  git add failed: {out}")
        return False

    logger.info(f"  📝 Committing: {commit_msg}")
    ok, out = run_git(["commit", "-m", commit_msg], repo, logger)
    if not ok:
        logger.error(f"     ✗  git commit failed: {out}")
        return False

    logger.info(f"  🚀 Pushing to origin/{branch} …")
    ok, out = run_git(["push", "origin", branch], repo, logger)
    if not ok:
        logger.error(f"     ✗  git push failed: {out}")
        return False

    logger.info(f"     ✓  Push successful.")
    return True


# ── Main Sync Job ──────────────────────────────────────────────────────────────
def sync_job(config: dict, logger: logging.Logger) -> None:
    """Full sync cycle: pull → forward → commit → push."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sep = "─" * 62

    logger.info(sep)
    logger.info(f"🔄  SYNC STARTED  —  {now}")
    logger.info(sep)

    upstreams = config["upstream"].get("upstreams", [])
    forwards  = config["path_forward"].get("forwards", [])
    git_cfg   = config["automation"].get("git", {})

    branch   = git_cfg.get("branch", "main")
    msg_tmpl = git_cfg.get("commit_message", "sync: auto-update [{datetime}]")
    commit_msg = msg_tmpl.replace(
        "[{datetime}]",
        datetime.now().strftime("%Y-%m-%d %H:%M"),
    )

    # ── Step 1: Pull upstreams ──────────────────────────────────────────────
    logger.info("📥 STEP 1 — Pulling upstream repositories")
    pull_results = pull_upstreams(upstreams, logger)
    ok_pulls = sum(pull_results.values())

    # ── Step 2: Forward skills ──────────────────────────────────────────────
    logger.info("📁 STEP 2 — Forwarding skill paths")
    copied = forward_skills(forwards, logger)

    # ── Step 3: Push to own repo ────────────────────────────────────────────
    logger.info("🚀 STEP 3 — Committing & pushing to own repo")
    push_ok = push_repo(REPO_ROOT, commit_msg, branch, logger)

    # ── Summary ─────────────────────────────────────────────────────────────
    logger.info(sep)
    status_icon = "✅" if push_ok else "⚠️ "
    logger.info(
        f"{status_icon} SYNC COMPLETE  |  "
        f"Upstreams pulled: {ok_pulls}/{len(pull_results)}  |  "
        f"Skills copied: {len(copied)}  |  "
        f"Push: {'OK' if push_ok else 'FAILED'}"
    )
    if copied:
        logger.info(f"   Skills synced: {', '.join(copied)}")
    logger.info(sep + "\n")


# ── Entry Point ────────────────────────────────────────────────────────────────
def main() -> None:
    # Load all configs
    upstream_cfg    = load_yaml(UPSTREAM_CONFIG)
    path_fwd_cfg    = load_yaml(PATH_FORWARD_CONFIG)
    automation_cfg  = load_yaml(AUTOMATION_CONFIG)

    config = {
        "upstream":     upstream_cfg,
        "path_forward": path_fwd_cfg,
        "automation":   automation_cfg,
    }

    # Setup logging
    log_cfg  = automation_cfg.get("logging", {})
    log_lvl  = log_cfg.get("level", "INFO")
    log_file = Path(log_cfg.get("log_file", str(LOGS_DIR / "sync.log")))
    logger   = setup_logging(log_lvl, log_file)

    # Schedule config
    sched_cfg      = automation_cfg.get("schedule", {})
    run_at         = sched_cfg.get("run_at")          # e.g. "06:00"
    interval_hours = sched_cfg.get("interval_hours", 24)

    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║          Human Skills — Upstream Sync Daemon                ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    logger.info(f"  Repo root  : {REPO_ROOT}")
    logger.info(f"  Upstreams  : {len(upstream_cfg.get('upstreams', []))}")
    logger.info(f"  Forwards   : {len(path_fwd_cfg.get('forwards', []))}")
    logger.info(f"  Schedule   : {'daily at ' + run_at if run_at else f'every {interval_hours}h'}")
    logger.info(f"  Log file   : {log_file}")
    logger.info("")

    # Run once immediately at startup
    sync_job(config, logger)

    # Register schedule
    if run_at:
        schedule.every().day.at(run_at).do(sync_job, config=config, logger=logger)
        logger.info(f"⏰  Next run scheduled daily at {run_at}")
    else:
        schedule.every(interval_hours).hours.do(sync_job, config=config, logger=logger)
        logger.info(f"⏰  Next run scheduled every {interval_hours} hours")

    # Keep the daemon alive
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
