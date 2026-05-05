#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          Human Skills — Upstream Sync Daemon  (Hot-Reload Edition)         ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  • Watches helpers/*.yaml for changes every 30 s (no restart needed)       ║
║  • Reloads config on any YAML edit — new upstreams, paths, schedule all    ║
║    take effect automatically on the next cycle                             ║
║                                                                            ║
║  Run inside a screen session:                                              ║
║    screen -S human-skills-sync                                             ║
║    python3 scripts/sync.py                                                 ║
║    Ctrl+A, D   (detach)                                                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
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
MANAGED_SKILLS_FILE = HELPERS_DIR / "managed_skills.json"

CONFIG_FILES = [UPSTREAM_CONFIG, PATH_FORWARD_CONFIG, AUTOMATION_CONFIG]


# ══════════════════════════════════════════════════════════════════════════════
# Config Watcher — detects YAML changes and hot-reloads
# ══════════════════════════════════════════════════════════════════════════════

class ConfigWatcher:
    """
    Tracks mtime of all three YAML files.
    Call has_changed() to detect edits, then reload() to pull the new config.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self._mtimes: dict[str, float] = {}
        self.config: dict = {}
        self._do_load()

    # ── Internal helpers ───────────────────────────────────────────────────
    @staticmethod
    def _read_yaml(path: Path) -> dict:
        if not path.exists():
            print(f"[ERROR] Config not found: {path}", file=sys.stderr)
            sys.exit(1)
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}

    @staticmethod
    def _resolve(obj: object) -> object:
        """
        Recursively replace {REPO_ROOT} in every string value inside
        a nested dict/list structure. Makes configs portable across machines.
        """
        repo = str(REPO_ROOT)
        if isinstance(obj, str):
            return obj.replace("{REPO_ROOT}", repo)
        if isinstance(obj, dict):
            return {k: ConfigWatcher._resolve(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [ConfigWatcher._resolve(i) for i in obj]
        return obj

    def _snapshot_mtimes(self) -> None:
        for p in CONFIG_FILES:
            self._mtimes[str(p)] = p.stat().st_mtime if p.exists() else 0.0

    def _do_load(self) -> None:
        self.config = {
            "upstream":     self._resolve(self._read_yaml(UPSTREAM_CONFIG)),
            "path_forward": self._resolve(self._read_yaml(PATH_FORWARD_CONFIG)),
            "automation":   self._resolve(self._read_yaml(AUTOMATION_CONFIG)),
        }
        self._snapshot_mtimes()

    # ── Schedule params helpers ────────────────────────────────────────────
    def sched_params(self) -> tuple[str | None, int]:
        """Return (run_at, interval_minutes) from automation.yaml."""
        sched = self.config["automation"].get("schedule", {})
        return sched.get("run_at"), sched.get("interval_minutes", 10)

    @property
    def poll_interval(self) -> int:
        """Seconds between hot-reload checks — read live from automation.yaml."""
        return self.config["automation"].get("schedule", {}).get("poll_interval_seconds", 30)

    # ── Public API ─────────────────────────────────────────────────────────
    def has_changed(self) -> bool:
        """True if any config file was modified since last load."""
        for p in CONFIG_FILES:
            mtime = p.stat().st_mtime if p.exists() else 0.0
            if self._mtimes.get(str(p)) != mtime:
                return True
        return False

    def reload(self) -> dict[str, dict]:
        """
        Reload all YAML files and return a dict describing what changed.
        Keys: 'upstream_count', 'forward_count', 'schedule'
        """
        old_sched    = self.sched_params()
        old_upstream = len(self.config["upstream"].get("upstreams", []))
        old_forward  = len(self.config["path_forward"].get("forwards", []))

        self._do_load()

        new_sched    = self.sched_params()
        new_upstream = len(self.config["upstream"].get("upstreams", []))
        new_forward  = len(self.config["path_forward"].get("forwards", []))

        changes: dict[str, dict] = {}

        if old_upstream != new_upstream:
            changes["upstreams"] = {"before": old_upstream, "after": new_upstream}

        if old_forward != new_forward:
            changes["forwards"] = {"before": old_forward, "after": new_forward}

        if old_sched != new_sched:
            changes["schedule"] = {
                "before": old_sched,
                "after":  new_sched,
            }

        return changes


# ══════════════════════════════════════════════════════════════════════════════
# Logging
# ══════════════════════════════════════════════════════════════════════════════

def setup_logging(level: str, log_file: Path) -> logging.Logger:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("human-skills")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    for handler in [logging.StreamHandler(sys.stdout),
                    logging.FileHandler(log_file, encoding="utf-8")]:
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger


# ══════════════════════════════════════════════════════════════════════════════
# Git helpers
# ══════════════════════════════════════════════════════════════════════════════

def run_git(args: list[str], cwd: Path, logger: logging.Logger) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["git"] + args, cwd=cwd,
            capture_output=True, text=True, timeout=120,
        )
        if r.returncode == 0:
            return True, r.stdout.strip()
        return False, (r.stderr.strip() or r.stdout.strip())
    except subprocess.TimeoutExpired:
        return False, "git timed out after 120 s"
    except Exception as exc:
        return False, str(exc)


def repo_is_dirty(repo: Path, logger: logging.Logger) -> bool:
    ok, out = run_git(["status", "--porcelain"], repo, logger)
    return ok and bool(out.strip())


# ══════════════════════════════════════════════════════════════════════════════
# Sync steps
# ══════════════════════════════════════════════════════════════════════════════

def pull_upstreams(upstreams: list[dict], logger: logging.Logger) -> tuple[dict[str, bool], list[str]]:
    results: dict[str, bool] = {}
    updated_upstreams: list[str] = []
    
    for entry in upstreams:
        name = entry.get("name", "unnamed")
        path = Path(entry.get("path", ""))
        url  = entry.get("url", "")
        pull_enabled = entry.get("pull", True)
        
        if not pull_enabled:
            logger.info(f"  ⏭  [{name}] Pull disabled — skipping update")
            results[name] = True  # Consider it successful since we intentionally skipped
            continue
            
        if not path.exists():
            if url:
                logger.info(f"  ↓  Cloning [{name}] from {url} …")
                path.parent.mkdir(parents=True, exist_ok=True)
                ok, out = run_git(["clone", url, str(path)], path.parent, logger)
                if ok:
                    logger.info(f"     ✓  Cloned successfully")
                    updated_upstreams.append(name)
                else:
                    logger.error(f"     ✗  Failed to clone: {out}")
                results[name] = ok
                continue
            else:
                logger.warning(f"  ⚠  [{name}] path missing and no URL provided — skipping: {path}")
                results[name] = False
                continue
                
        logger.info(f"  ↓  Pulling [{name}] …")
        ok, out = run_git(["pull"], path, logger)
        if ok:
            tag = "already up to date" if "Already up to date" in out else (out or "updated")
            logger.info(f"     ✓  {tag}")
            if "Already up to date" not in out:
                updated_upstreams.append(name)
        else:
            logger.error(f"     ✗  {out}")
        results[name] = ok
        
    return results, updated_upstreams


def load_registry() -> set[str]:
    """Loads the set of managed skill paths from JSON."""
    if not MANAGED_SKILLS_FILE.exists():
        return set()
    try:
        with open(MANAGED_SKILLS_FILE, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_registry(paths: set[str]) -> None:
    """Saves the set of managed skill paths to JSON."""
    MANAGED_SKILLS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANAGED_SKILLS_FILE, "w") as f:
        json.dump(sorted(list(paths)), f, indent=4)


def forward_skills(forwards: list[dict], logger: logging.Logger) -> tuple[list[str], set[str]]:
    copied: list[str] = []
    cleared_dsts: set[str] = set()
    touched_dsts: set[str] = set()

    for rule in forwards:
        if not rule.get("enabled", True):
            continue
            
        src_path_str = rule.get("from", "")
        dst_path_str = rule.get("to", "")
        
        src  = Path(src_path_str)
        dst  = Path(dst_path_str)
        name = src.name
        
        if not src.exists():
            logger.warning(f"  ⚠  Source missing — skipping: {src}")
            continue
            
        # Record this destination as managed (relative to REPO_ROOT if possible)
        try:
            rel_dst = dst.resolve().relative_to(REPO_ROOT.resolve())
            touched_dsts.add(str(rel_dst))
        except ValueError:
            touched_dsts.add(str(dst.resolve()))
            
        logger.info(f"  →  Forwarding [{name}] …")
        try:
            if src.is_file():
                if dst.is_dir() or dst_path_str.endswith("/") or dst_path_str.endswith("\\"):
                    dst.mkdir(parents=True, exist_ok=True)
                    actual_dst = dst / name
                else:
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    actual_dst = dst
                    
                shutil.copy2(src, actual_dst)
                logger.info(f"     ✓  [File] {src} → {actual_dst}")
                copied.append(name)
                
            elif src.is_dir():
                resolved_dst = str(dst.resolve())
                if resolved_dst not in cleared_dsts:
                    if dst.exists():
                        shutil.rmtree(dst)
                    cleared_dsts.add(resolved_dst)
                    
                shutil.copytree(src, dst, dirs_exist_ok=True)
                logger.info(f"     ✓  [Dir]  {src} → {dst}")
                copied.append(name)
                
        except Exception as exc:
            logger.error(f"     ✗  {exc}")
            
    return copied, touched_dsts


def commit_and_push(
    repo: Path,
    upstream_changes: dict[str, list[str]],
    manual_changes: list[str],
    branch: str,
    logger: logging.Logger,
    current_time: str
) -> bool:
    if not repo_is_dirty(repo, logger):
        logger.info("  ✓  Nothing to commit — repo is clean.")
        return True

    # 1. Commit per upstream
    for up_name, files in upstream_changes.items():
        if not files:
            continue
        ok_add, out_add = run_git(["add", "--all", "--"] + files, repo, logger)
        if not ok_add:
            logger.error(f"     ✗  git add failed for {up_name}: {out_add}")
        msg = f"sync: auto-update from {up_name} {current_time}"
        logger.info(f"  📝 Committing {len(files)} files for [{up_name}] …")
        ok_cmt, out_cmt = run_git(["commit", "-m", msg], repo, logger)
        if not ok_cmt:
            logger.error(f"     ✗  git commit failed for {up_name}: {out_cmt}")

    # 2. Commit manual changes
    if manual_changes:
        ok_add, out_add = run_git(["add", "--all", "--"] + manual_changes, repo, logger)
        if not ok_add:
            logger.error(f"     ✗  git add failed for manual changes: {out_add}")
        msg = f"chore: manual update of {len(manual_changes)} file(s) {current_time}"
        logger.info(f"  📝 Committing {len(manual_changes)} manual changes …")
        ok_cmt, out_cmt = run_git(["commit", "-m", msg], repo, logger)
        if not ok_cmt:
            logger.error(f"     ✗  git commit failed for manual changes: {out_cmt}")

    # 3. Catch-all for any missed files
    ok, status_out = run_git(["status", "--porcelain"], repo, logger)
    if ok and status_out.strip():
        ok_add, out_add = run_git(["add", "."], repo, logger)
        if not ok_add:
            logger.error(f"     ✗  git add . failed: {out_add}")
        msg = f"sync: catch-all cleanup {current_time}"
        logger.info(f"  📝 Committing remaining catch-all changes …")
        ok_cmt, out_cmt = run_git(["commit", "-m", msg], repo, logger)
        if not ok_cmt:
            logger.error(f"     ✗  git commit failed for catch-all: {out_cmt}")

    # 4. Push
    logger.info(f"  🚀 Pushing → origin/{branch} …")
    ok, out = run_git(["push", "origin", branch], repo, logger)
    if not ok:
        logger.error(f"     ✗  {out}")
        return False
        
    logger.info("     ✓  Push successful.")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# Main sync job — always reads from the live watcher.config
# ══════════════════════════════════════════════════════════════════════════════

def sync_job(watcher: ConfigWatcher, logger: logging.Logger) -> None:
    cfg      = watcher.config          # always the latest config
    sep      = "─" * 62
    now      = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    git_cfg  = cfg["automation"].get("git", {})
    branch   = git_cfg.get("branch", "main")

    logger.info(sep)
    logger.info(f"🔄  SYNC STARTED  —  {now}")
    logger.info(sep)

    # Step 0
    logger.info("⬇️  STEP 0 — Pulling main repository (human-skills)")
    pull_args = ["pull", "--rebase", "--autostash", "origin", branch]
    ok, out = run_git(pull_args, REPO_ROOT, logger)
    if ok:
        logger.info(f"     ✓  Main repo updated: {out or 'Already up to date'}")
    else:
        logger.error(f"     ✗  Failed to pull main repo: {out}")
        logger.warning("        Push step may fail later due to this.")

    # Step 1
    logger.info("📥 STEP 1 — Pulling upstream repositories")
    pulls, updated_upstreams = pull_upstreams(cfg["upstream"].get("upstreams", []), logger)

    # Step 2
    logger.info("📁 STEP 2 — Forwarding skill paths")
    # Load what we managed previously
    previous_managed = load_registry()
    
    # Run forward and get current managed paths
    copied, current_managed = forward_skills(cfg["path_forward"].get("forwards", []), logger)

    # Step 2.5 — Orphan Cleanup
    logger.info("🧹 STEP 2.5 — Cleaning up orphaned upstream skills")
    removed = []
    
    # Orphans = (Paths we managed before) - (Paths we touched now)
    orphans = previous_managed - current_managed
    
    for orphan_path_str in orphans:
        # Resolve path relative to REPO_ROOT if it's not absolute
        orphan_path = Path(orphan_path_str)
        if not orphan_path.is_absolute():
            orphan_path = REPO_ROOT / orphan_path
            
        if orphan_path.exists():
            logger.warning(f"  🗑️  Removing orphaned upstream skill: {orphan_path.name}")
            try:
                if orphan_path.is_dir():
                    shutil.rmtree(orphan_path)
                else:
                    orphan_path.unlink()
                removed.append(orphan_path.name)
            except Exception as exc:
                logger.error(f"     ✗  Failed to remove {orphan_path.name}: {exc}")
    
    # Update registry for next time
    save_registry(current_managed)

    # Step 3
    logger.info("🚀 STEP 3 — Committing & pushing to own repo")
    
    # Identify which upstreams actually caused modifications
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Check git status to find which forwards were updated
    ok, status_out = run_git(["status", "--porcelain"], REPO_ROOT, logger)
    
    manual_changes = []
    upstream_changes = {} # upstream_name -> list of relative file paths
    
    if ok and status_out.strip():
        forwards = cfg["path_forward"].get("forwards", [])
        upstreams = cfg["upstream"].get("upstreams", [])
        
        for line in status_out.splitlines():
            if len(line) < 4:
                continue
            # Extract path from line (e.g., " M skills/g2-chart-generator/SKILL.md")
            changed_file = line[3:].strip('"')
            changed_path = (REPO_ROOT / changed_file).resolve()
            
            matched_upstream = None
            for rule in forwards:
                if not rule.get("enabled", True) or not rule.get("to"):
                    continue
                dst = Path(rule["to"]).resolve()
                
                is_match = False
                try:
                    if changed_path == dst or changed_path.is_relative_to(dst):
                        is_match = True
                except AttributeError:
                    if str(changed_path).startswith(str(dst)):
                        is_match = True
                        
                if is_match and rule.get("from"):
                    src = Path(rule["from"]).resolve()
                    for up in upstreams:
                        up_path = Path(up.get("path", "")).resolve()
                        try:
                            if src == up_path or src.is_relative_to(up_path):
                                matched_upstream = up.get("name", "unknown")
                                break
                        except AttributeError:
                            if str(src).startswith(str(up_path)):
                                matched_upstream = up.get("name", "unknown")
                                break
                    if matched_upstream:
                        break
            
            if matched_upstream:
                upstream_changes.setdefault(matched_upstream, []).append(changed_file)
            else:
                manual_changes.append(changed_file)

    push_ok = commit_and_push(
        repo=REPO_ROOT,
        upstream_changes=upstream_changes,
        manual_changes=manual_changes,
        branch=branch,
        logger=logger,
        current_time=current_time
    )

    # Summary
    ok_cnt  = sum(pulls.values())
    icon    = "✅" if push_ok else "⚠️ "
    logger.info(sep)
    logger.info(
        f"{icon} SYNC COMPLETE  |  "
        f"Upstreams: {ok_cnt}/{len(pulls)}  |  "
        f"Skills: +{len(copied)} / -{len(removed)}  |  "
        f"Push: {'OK' if push_ok else 'FAILED'}"
    )
    if copied:
        logger.info(f"   Added: {', '.join(copied)}")
    if removed:
        logger.info(f"   Removed: {', '.join(removed)}")
    logger.info(sep + "\n")


# ══════════════════════════════════════════════════════════════════════════════
# Scheduler helpers
# ══════════════════════════════════════════════════════════════════════════════

def register_schedule(watcher: ConfigWatcher, logger: logging.Logger) -> None:
    """Clear all jobs and register sync_job with current schedule config."""
    schedule.clear()
    run_at, interval_minutes = watcher.sched_params()

    if run_at:
        schedule.every().day.at(run_at).do(sync_job, watcher=watcher, logger=logger)
        logger.info(f"⏰  Scheduled: daily at {run_at}")
    else:
        schedule.every(interval_minutes).minutes.do(sync_job, watcher=watcher, logger=logger)
        logger.info(f"⏰  Scheduled: every {interval_minutes} minute(s)")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    # Bootstrap: minimal console logger just for config loading errors
    boot_logger = logging.getLogger("human-skills-boot")
    boot_logger.setLevel(logging.INFO)
    boot_logger.propagate = False
    _bh = logging.StreamHandler(sys.stdout)
    _bh.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                        datefmt="%Y-%m-%d %H:%M:%S"))
    boot_logger.addHandler(_bh)

    watcher = ConfigWatcher(boot_logger)

    # Proper logger with console + file output
    log_cfg  = watcher.config["automation"].get("logging", {})
    log_file = Path(log_cfg.get("log_file", str(LOGS_DIR / "sync.log")))
    logger   = setup_logging(log_cfg.get("level", "INFO"), log_file)

    logger.info("╔══════════════════════════════════════════════════════════════╗")
    logger.info("║     Human Skills — Upstream Sync Daemon  (Hot-Reload)       ║")
    logger.info("╚══════════════════════════════════════════════════════════════╝")
    logger.info(f"  Repo root    : {REPO_ROOT}")
    logger.info(f"  Upstreams    : {len(watcher.config['upstream'].get('upstreams', []))}")
    logger.info(f"  Forwards     : {len(watcher.config['path_forward'].get('forwards', []))}")
    logger.info(f"  Config watch : every {watcher.poll_interval}s")
    logger.info(f"  Log file     : {log_file}")
    logger.info("")

    # Initial sync + schedule
    sync_job(watcher, logger)
    register_schedule(watcher, logger)

    # ── Main loop ──────────────────────────────────────────────────────────
    while True:
        time.sleep(watcher.poll_interval)
        schedule.run_pending()

        # Hot-reload check
        if watcher.has_changed():
            logger.info("🔁  Config change detected — hot-reloading …")
            changes = watcher.reload()

            if not changes:
                logger.info("   (no functional changes — content edit only)")
            else:
                for key, diff in changes.items():
                    if key == "schedule":
                        before_at, before_m = diff["before"]
                        after_at,  after_m  = diff["after"]
                        logger.info(
                            f"   📅 Schedule changed: "
                            f"{'@'+before_at if before_at else str(before_m)+'m'} → "
                            f"{'@'+after_at  if after_at  else str(after_m) +'m'}"
                        )
                    elif key == "upstreams":
                        logger.info(
                            f"   📦 Upstreams: {diff['before']} → {diff['after']}"
                        )
                    elif key == "forwards":
                        logger.info(
                            f"   🔀 Forwards: {diff['before']} → {diff['after']}"
                        )

            # Always reschedule in case timing changed
            register_schedule(watcher, logger)
            
            # TRIGGER IMMEDIATE SYNC:
            # Since the user edited the config, they likely want to see the 
            # results immediately rather than waiting for the next scheduled run.
            logger.info("   ⚡ Triggering immediate sync due to config change …")
            sync_job(watcher, logger)
            
            logger.info("   ✓  Hot-reload complete — new config active\n")


if __name__ == "__main__":
    main()
 
