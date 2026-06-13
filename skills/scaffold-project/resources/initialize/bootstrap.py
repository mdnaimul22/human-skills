#!/usr/bin/env python3

import os
import sys
import urllib.request
from pathlib import Path
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
    "project-config-example.md",
    "project-tree-example.md"
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
        "src/core/__init__.py",
        "src/core/auth.py",
        "src/db/__init__.py",
        "src/db/models.py",
        "src/db/repositories.py",
        "src/providers/__init__.py",
        "src/schema/__init__.py",
        "src/schema/auth.py",
        "src/services/__init__.py",
        "src/services/auth.py",
        "src/routers/__init__.py",
        "src/routers/auth.py",
        "tests/__init__.py"
    ]
    for path_str in src_templates:
        tpl_path = Path(__file__).resolve().parent / path_str
        if tpl_path.exists():
            dest_path = Path(path_str)
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            dest_path.write_text(tpl_path.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"   [Scaffolded] {path_str}")

def sync_rules():
    """4. Sync Rules"""
    print("📥 Syncing Rules from human-skills...")
    for filename in FILES:
        url = f"{REPO_RAW_URL}/.agents/rules/{filename}"
        dest = RULES_DIR / filename
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode("utf-8")
                dest.write_text(content, encoding="utf-8")
            print(f"   [Synced] {filename}")
        except Exception as e:
            print(f"   [Failed] {filename} - {e}")

def scaffold_human_skills():
    """5. Scaffold config and helpers via human-skills"""
    print("🤖 Integrating human-skills scaffolding tools...")
    
    # Run setconfig
    try:
        print("   [Running] setconfig...")
        subprocess.run(
            ["human-skills", '{"tool_name": "setconfig", "tool_args": {"destination": "src/config"}}'], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        print("   ✅ scaffolded src/config/")
    except subprocess.CalledProcessError:
        print("   ❌ Failed to scaffold config layer (is human-skills installed globally?)")
    except FileNotFoundError:
        print("   ❌ human-skills command not found. Skipping auto-scaffold.")

    # Run sethelpers
    try:
        print("   [Running] sethelpers...")
        subprocess.run(
            ["human-skills", '{"tool_name": "sethelpers", "tool_args": {"destination": "src/helpers"}}'], 
            check=True, 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        print("   ✅ scaffolded src/helpers/")
    except subprocess.CalledProcessError:
        print("   ❌ Failed to scaffold helpers layer.")
    except FileNotFoundError:
        pass

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
