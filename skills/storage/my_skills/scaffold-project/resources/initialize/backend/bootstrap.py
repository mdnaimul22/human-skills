#!/usr/bin/env python3

import os
import sys
import shutil
import urllib.request
import tarfile
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

REPO_URL = "https://github.com/mdnaimul22/human-skills.git"
TAR_URL = "https://github.com/mdnaimul22/human-skills/archive/refs/heads/main.tar.gz"
BACKEND_REL_PATH = "skills/storage/my_skills/scaffold-project/resources/initialize/backend"

SKIP_DIRS = {"__pycache__", ".pytest_cache", ".venv", "venv", ".git", "logs", "tmp"}
SKIP_FILES = {"bootstrap.py", ".DS_Store"}
ALLOWED_DATA_SUBDIRS = {"agents"}


def _should_copy_file(rel: Path) -> bool:
    if rel.name in SKIP_FILES or rel.name.endswith(".db"):
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] == "env":
        return rel.name.endswith(".example")
    if parts[0] == "data":
        return len(parts) >= 2 and parts[1] in ALLOWED_DATA_SUBDIRS
    return True


def check_empty_directory():
    print("🚀 Starting Project Bootstrap...")
    items = os.listdir(".")
    if items and items != [".git"]:
        print("⚠️  Error: This directory is not empty!")
        print("❌ Sorry, this module is for initializing new projects only.")
        sys.exit(1)


def _find_repo_root(start_dir: Optional[Path]) -> Optional[Path]:
    if not start_dir:
        return None
    for p in [start_dir, *start_dir.parents]:
        if (p / ".agents" / "rules").exists() or (p / "skills" / "storage").exists():
            return p
    return None


def copy_tree_dynamic(source_dir: Path, target_dir: Path) -> list[str]:
    copied = []
    for item in sorted(source_dir.rglob("*")):
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        if not item.is_file():
            continue
        rel = item.relative_to(source_dir)
        if not _should_copy_file(rel):
            continue
        dest = target_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item, dest)
        copied.append(str(rel))
        print(f"   [Scaffolded] {rel}")

    target_env_dir = target_dir / "env"
    if target_env_dir.exists():
        for example_file in sorted(target_env_dir.glob("*.example")):
            active_name = example_file.name[:-len(".example")]
            active_path = target_env_dir / active_name
            if active_name and not active_path.exists():
                shutil.copy2(example_file, active_path)
                print(f"   [Created] env/{active_name} (from env/{example_file.name})")

    for d in ["logs", "docs", "data", "tmp", "env"]:
        (target_dir / d).mkdir(parents=True, exist_ok=True)

    return copied


def fetch_remote_archive(tmp_dir: Path) -> Optional[Path]:
    if shutil.which("git"):
        try:
            repo_dest = tmp_dir / "repo"
            cmd = [
                "git", "clone", "--depth", "1", "--filter=blob:none", "--sparse",
                REPO_URL, str(repo_dest)
            ]
            if subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                sparse_cmd = ["git", "sparse-checkout", "set", ".agents", BACKEND_REL_PATH]
                subprocess.run(sparse_cmd, cwd=str(repo_dest), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if (repo_dest / ".agents").exists():
                    return repo_dest
        except Exception:
            pass

    try:
        archive_path = tmp_dir / "archive.tar.gz"
        req = urllib.request.Request(TAR_URL, headers={"User-Agent": "human-skills-bootstrap"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            archive_path.write_bytes(resp.read())

        with tarfile.open(archive_path, "r:gz") as tar:
            try:
                tar.extractall(path=tmp_dir, filter="data")
            except TypeError:
                tar.extractall(path=tmp_dir)

        for candidate in tmp_dir.iterdir():
            if candidate.is_dir() and candidate.name.startswith("human-skills"):
                return candidate
    except Exception as e:
        print(f"⚠️  Remote archive fetch failed: {e}")

    return None


def scaffold_backend():
    print("📁 Scaffolding backend structure...")
    target_dir = Path.cwd()

    try:
        current_dir = Path(__file__).resolve().parent
    except NameError:
        current_dir = None

    if current_dir and current_dir.exists() and (current_dir / "main.py").exists():
        copy_tree_dynamic(current_dir, target_dir)
        return

    print("🌐 Local templates not found. Fetching from remote repository...")
    with tempfile.TemporaryDirectory() as tmp:
        remote_root = fetch_remote_archive(Path(tmp))
        if remote_root:
            backend_src = remote_root / BACKEND_REL_PATH
            if backend_src.exists():
                copy_tree_dynamic(backend_src, target_dir)
                return

    print("❌ Failed to scaffold backend files.")
    sys.exit(1)


def sync_rules():
    print("📥 Syncing Rules from human-skills...")
    target_agents = Path.cwd() / ".agents"
    target_agents.mkdir(parents=True, exist_ok=True)

    try:
        current_dir = Path(__file__).resolve().parent
        repo_root = _find_repo_root(current_dir)
        local_agents = (repo_root / ".agents") if repo_root else None
    except NameError:
        local_agents = None

    if local_agents and local_agents.exists():
        for item in sorted(local_agents.rglob("*")):
            if any(part in SKIP_DIRS for part in item.parts):
                continue
            if item.is_file():
                rel = item.relative_to(local_agents)
                dest = target_agents / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, dest)
                print(f"   [Synced local] .agents/{rel}")
        return

    print("🌐 Local .agents not found. Syncing rules from remote repository...")
    with tempfile.TemporaryDirectory() as tmp:
        remote_root = fetch_remote_archive(Path(tmp))
        if remote_root:
            source_agents = remote_root / ".agents"
            if source_agents.exists():
                for item in sorted(source_agents.rglob("*")):
                    if any(part in SKIP_DIRS for part in item.parts):
                        continue
                    if item.is_file():
                        rel = item.relative_to(source_agents)
                        dest = target_agents / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(item, dest)
                        print(f"   [Synced remote] .agents/{rel}")
                return

    print("⚠️  Warning: Failed to sync rules directory.")


def main():
    check_empty_directory()
    scaffold_backend()
    sync_rules()
    print("\n✨ Project Bootstrap Completed Successfully!")
    print("Happy Coding! 🎯")


if __name__ == "__main__":
    main()
