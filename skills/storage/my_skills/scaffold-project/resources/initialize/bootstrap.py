#!/usr/bin/env python3

import os
import sys
import urllib.request
import shutil
from pathlib import Path
from typing import Optional
import subprocess

# Configuration
REPO_RAW_URL = "https://raw.githubusercontent.com/mdnaimul22/human-skills/main"
RULES_DIR = Path(".agents/rules")
FILES = [
    "coding-standards.md",
    "architecture-patterns.md",
    "maintenance-testing.md",
    "config-path-rules.md",
    "config-usage-rules.md",
    "helpers-usage-rules.md",
    "project-config-example.md",
    "project-tree-example.md",
    "common-git-workflow.md"
]

def check_empty_directory():
    """Safety Check: Ensure the directory is empty"""
    print("🚀 Starting Project Bootstrap...")
    items = os.listdir('.')
    if items:
        # Ignore hidden git dir if any, but let's be strict as bash was
        if items != ['.git']:
            print("⚠️  Error: This directory is not empty!")
            print("❌ Sorry, this module is for initializing new projects only. Running it in an existing project may result in data loss or configuration overwrite.")
            sys.exit(1)

def create_directories():
    """1. Create Directory Structure"""
    print("📁 Creating directories...")
    dirs = [
        "docs",
        "logs",
        "deploy/nginx",
        "scripts",
        "src/config",
        "src/core",
        "src/db",
        "src/db/repositories",
        "src/helpers",
        "src/providers",
        "src/schema",
        "src/services",
        "src/routers",
        "tests",
        str(RULES_DIR)
    ]
    
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        print(f"   [Created] {d}")

def create_init_file(path_str: str, msg: str):
    path = Path(path_str)
    content = f'"""\n{msg}\n"""\n'
    path.write_text(content, encoding="utf-8")
    print(f"   [Created] {path_str}")

def create_init_files():
    """2. Create __init__.py files with conventions"""
    print("📄 Initializing Python packages with conventions...")
    
    create_init_file("src/__init__.py", "Global source package.")

def _find_repo_root(start_dir: Optional[Path]) -> Optional[Path]:
    if not start_dir:
        return None
    for p in [start_dir, *start_dir.parents]:
        if (p / ".agents" / "rules").exists() or (p / "skills" / "storage").exists():
            return p
    return None

def create_base_files():
    """3. Create basic files"""
    print("📄 Creating base files...")
    
    # Ensure data directory exists for the SQLite database
    Path("data").mkdir(parents=True, exist_ok=True)

    # Copy template source files for DB/auth layer
    src_templates = [
        ".env",
        ".env.example",
        ".gitignore",
        "LICENSE",
        "main.py",
        "README.md",
        "requirements.txt",
        "deploy/nginx/nginx.conf.template",
        "scripts/generate_nginx_conf.py",
        "src/core/__init__.py",
        "src/core/auth.py",
        "src/db/__init__.py",
        "src/db/connection.py",
        "src/db/models.py",
        "src/db/repository.py",
        "src/db/repositories.py",
        "src/helpers/__init__.py",
        "src/helpers/cors.py",
        "src/helpers/date_utils.py",
        "src/helpers/error_handlers.py",
        "src/helpers/exceptions.py",
        "src/helpers/frontend_runner.py",
        "src/helpers/middleware.py",
        "src/helpers/nginx.py",
        "src/helpers/port_utils.py",
        "src/helpers/rate_limit.py",
        "src/helpers/retry.py",
        "src/providers/__init__.py",
        "src/providers/email.py",
        "src/providers/tailscale.py",
        "src/schema/__init__.py",
        "src/schema/auth.py",
        "src/services/__init__.py",
        "src/services/auth.py",
        "src/routers/__init__.py",
        "src/routers/auth.py",
        "src/routers/dependencies.py",
        "tests/__init__.py"
    ]
    
    try:
        current_dir = Path(__file__).resolve().parent
    except NameError:
        current_dir = None

    for path_str in src_templates:
        dest_path = Path(path_str)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        success = False
        if current_dir:
            tpl_path = current_dir / path_str
            if tpl_path.exists():
                try:
                    dest_path.write_text(tpl_path.read_text(encoding="utf-8"), encoding="utf-8")
                    print(f"   [Scaffolded local] {path_str}")
                    success = True
                except Exception as e:
                    print(f"   [Failed local copy] {path_str} - {e}, falling back to download")

        if not success:
            remote_path_str = ".env.example" if path_str == ".env" else path_str
            url = f"{REPO_RAW_URL}/skills/storage/my_skills/scaffold-project/resources/initialize/{remote_path_str}"
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    content = response.read().decode("utf-8")
                    dest_path.write_text(content, encoding="utf-8")
                print(f"   [Downloaded] {path_str}")
            except Exception as e:
                print(f"   [Failed] {path_str} - {e}")

def sync_rules():
    """4. Sync Rules"""
    print("📥 Syncing Rules from human-skills...")
    
    try:
        current_dir = Path(__file__).resolve().parent
        repo_root = _find_repo_root(current_dir)
        local_rules_dir = (repo_root / ".agents" / "rules") if repo_root else None
    except NameError:
        local_rules_dir = None
    
    # If local repo is found, dynamically sync all .md files
    if local_rules_dir and local_rules_dir.exists():
        for local_file in sorted(local_rules_dir.glob("*.md")):
            dest = RULES_DIR / local_file.name
            try:
                shutil.copy2(local_file, dest)
                print(f"   [Copied local] {local_file.name}")
            except Exception as e:
                print(f"   [Failed to copy local] {local_file.name} - {e}")
        return

    # Fallback to dynamic GitHub API discovery / predefined list
    rule_files = list(FILES)
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/mdnaimul22/human-skills/contents/.agents/rules",
            headers={"User-Agent": "human-skills-bootstrap"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            import json
            items = json.loads(response.read().decode("utf-8"))
            dynamic_list = [x["name"] for x in items if isinstance(x, dict) and x.get("type") == "file" and x.get("name", "").endswith(".md")]
            if dynamic_list:
                rule_files = dynamic_list
    except Exception:
        pass

    for filename in rule_files:
        dest = RULES_DIR / filename
        url = f"{REPO_RAW_URL}/.agents/rules/{filename}"
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode("utf-8")
                dest.write_text(content, encoding="utf-8")
            print(f"   [Downloaded] {filename}")
        except Exception as e:
            print(f"   [Failed] {filename} - {e}")

def scaffold_human_skills():
    """5. Scaffold config and helpers via human-skills"""
    print("🤖 Integrating human-skills scaffolding tools...")
    
    # Run setconfig
    config_success = False
    try:
        print("   [Running] setconfig...")
        subprocess.run(
            ["human-skills", '{"tool_name": "setconfig", "tool_args": {"destination": "src/config"}}'], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        print("   ✅ scaffolded src/config/")
        config_success = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    if not config_success:
        try:
            current_dir = Path(__file__).resolve().parent
            repo_root = _find_repo_root(current_dir)
            local_config_dir = (repo_root / "skills" / "storage" / "my_skills" / "scaffold-config" / "resources" / "config") if repo_root else None
        except NameError:
            local_config_dir = None

        config_files = ["__init__.py", "dotenv.py", "files.py", "logger.py", "paths.py", "settings.py"]
        
        if local_config_dir and local_config_dir.exists():
            print("   [Fallback] Copying config layer locally...")
            try:
                for f in config_files:
                    shutil.copy2(local_config_dir / f, Path("src/config") / f)
                print("   ✅ scaffolded src/config/ (local)")
                config_success = True
            except Exception as e:
                print(f"   ❌ Local config copy failed - {e}, falling back to download")

        if not config_success:
            print("   [Fallback] Downloading config layer from GitHub...")
            for f in config_files:
                url = f"{REPO_RAW_URL}/skills/storage/my_skills/scaffold-config/resources/config/{f}"
                dest_path = Path("src/config") / f
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with urllib.request.urlopen(url, timeout=10) as response:
                        content = response.read().decode("utf-8")
                        dest_path.write_text(content, encoding="utf-8")
                    print(f"      [Downloaded] config/{f}")
                except Exception as e:
                    print(f"      [Failed] config/{f} - {e}")

def main():
    check_empty_directory()
    create_directories()
    create_init_files()
    create_base_files()
    sync_rules()
    scaffold_human_skills()
    
    print("\n✨ Project Bootstrap Completed Successfully!")
    print("Happy Coding! 🎯")

if __name__ == "__main__":
    main()
