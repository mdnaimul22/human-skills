#!/usr/bin/env python3
"""Auto Dependency & Requirements Generator.

Recursively scans any Python project using Abstract Syntax Trees (AST),
filters out Python standard library and local project modules, resolves PyPI
package names and installed versions, and generates both requirements.txt
and pyproject.toml.

Usage:
    python tools/generate_requirements.py
    python tools/generate_requirements.py --path /path/to/project
    python tools/generate_requirements.py --exact
"""
import argparse
import ast
import importlib.metadata
import os
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Common import-to-PyPI package mapping for libraries where import != package name
KNOWN_PACKAGE_MAP: Dict[str, str] = {
    "cv2": "opencv-python",
    "pydantic_settings": "pydantic-settings",
    "dotenv": "python-dotenv",
    "PIL": "pillow",
    "yaml": "pyyaml",
    "sklearn": "scikit-learn",
    "skimage": "scikit-image",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "jose": "python-jose",
    "multipart": "python-multipart",
    "magic": "python-magic",
    "jwt": "pyjwt",
    "pytest_asyncio": "pytest-asyncio",
    "faster_whisper": "faster-whisper",
    "serial": "pyserial",
    "fitz": "pymupdf",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "websocket": "websocket-client",
}

# Directories to always ignore when scanning
IGNORED_DIRS: Set[str] = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    ".eggs",
    ".agents",
    "backup",
    "archive",
    "output",
    "data",
    "logs",
    "web",
}

# Development and testing package names
DEV_PACKAGES: Set[str] = {
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "pytest-mock",
    "black",
    "flake8",
    "mypy",
    "isort",
    "ruff",
    "pylint",
    "coverage",
    "tox",
}


def get_stdlib_modules() -> Set[str]:
    """Retrieve all Python standard library module names."""
    if hasattr(sys, "stdlib_module_names"):
        return set(sys.stdlib_module_names)
    # Fallback for Python < 3.10
    import distutils.sysconfig
    stdlib_dir = distutils.sysconfig.get_python_lib(standard_lib=True)
    names = set()
    for item in os.listdir(stdlib_dir):
        if item.endswith(".py"):
            names.add(item[:-3])
        elif os.path.isdir(os.path.join(stdlib_dir, item)):
            names.add(item)
    return names


def discover_local_modules(project_root: Path) -> Set[str]:
    """Identify local package directories and root python scripts so they aren't marked as third-party."""
    local_names: Set[str] = set()
    for item in project_root.iterdir():
        if item.name.startswith(".") or item.name in IGNORED_DIRS:
            continue
        if item.is_dir():
            # Any dir with a .py file or __init__.py is a local package/module
            has_py = any(f.suffix == ".py" for f in item.rglob("*.py"))
            if has_py:
                local_names.add(item.name)
        elif item.suffix == ".py":
            local_names.add(item.stem)
    return local_names


def extract_imports_from_file(file_path: Path) -> Set[str]:
    """Parse a python file using AST and return top-level imported module names."""
    imported_modules: Set[str] = set()
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content, filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top:
                        imported_modules.add(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:  # Absolute imports only
                    top = node.module.split(".")[0]
                    if top:
                        imported_modules.add(top)
    except Exception as e:
        print(f"  ⚠️ Warning: Could not parse {file_path.name}: {e}")
    return imported_modules


def scan_project_imports(project_root: Path) -> Set[str]:
    """Scan all Python files across the project directory."""
    all_imports: Set[str] = set()
    stdlib = get_stdlib_modules()
    local_mods = discover_local_modules(project_root)

    print(f"🔍 Scanning Python files in: {project_root.resolve()}")
    count_files = 0
    for root_dir, dirs, files in os.walk(project_root):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith(".")]
        for file in files:
            if file.endswith(".py"):
                count_files += 1
                f_path = Path(root_dir) / file
                file_imports = extract_imports_from_file(f_path)
                all_imports.update(file_imports)

    print(f"   • Scanned {count_files} Python source files.")

    # Filter out standard library and local project modules
    third_party = {
        m for m in all_imports
        if m not in stdlib and m not in local_mods and not m.startswith("_")
    }
    return third_party


def resolve_package_names(raw_modules: Set[str]) -> Dict[str, str]:
    """Map raw module import names to actual PyPI package distribution names."""
    # Attempt to use importlib metadata package distribution map
    pkg_dist_map = {}
    try:
        pkg_dist_map = importlib.metadata.packages_distributions()
    except Exception:
        pass

    resolved: Dict[str, str] = {}
    for mod in raw_modules:
        if mod in KNOWN_PACKAGE_MAP:
            resolved[mod] = KNOWN_PACKAGE_MAP[mod]
        elif mod in pkg_dist_map and pkg_dist_map[mod]:
            # Use the first mapped package distribution name
            resolved[mod] = pkg_dist_map[mod][0]
        else:
            # Fallback: treat import name as package name
            clean_name = mod.replace("_", "-")
            resolved[mod] = clean_name
    return resolved


def get_installed_versions(packages: Set[str], exact: bool = False) -> List[Tuple[str, str, bool]]:
    """Query current environment for package versions.
    
    Returns list of (pkg_name, version_spec, is_dev).
    """
    results = []
    for pkg in sorted(packages):
        is_dev = pkg.lower() in DEV_PACKAGES
        try:
            installed_ver = importlib.metadata.version(pkg)
            # Create version constraint
            if exact:
                spec = f"=={installed_ver}"
            else:
                parts = installed_ver.split(".")
                if len(parts) >= 2:
                    min_ver = f"{parts[0]}.{parts[1]}.0"
                else:
                    min_ver = f"{parts[0]}.0"
                spec = f">={min_ver}"
        except Exception:
            # Package not installed in current environment
            spec = ""

        results.append((pkg, spec, is_dev))
    return results


def categorize_packages(pkg_list: List[Tuple[str, str, bool]]) -> Dict[str, List[Tuple[str, str]]]:
    """Organize packages into functional categories."""
    categories: Dict[str, List[Tuple[str, str]]] = {
        "Core Numerical & Math": [],
        "Configuration & Schemas": [],
        "Deep Learning & AI Vision": [],
        "Web & Networking": [],
        "Development & Testing": [],
        "Other Utilities": [],
    }

    for pkg, spec, is_dev in pkg_list:
        p_lower = pkg.lower()
        if is_dev:
            categories["Development & Testing"].append((pkg, spec))
        elif p_lower in ("numpy", "scipy", "pandas", "opencv-python", "pillow"):
            categories["Core Numerical & Math"].append((pkg, spec))
        elif p_lower in ("pydantic", "pydantic-settings", "python-dotenv", "pyyaml", "dynaconf"):
            categories["Configuration & Schemas"].append((pkg, spec))
        elif p_lower in ("torch", "torchvision", "torchaudio", "ultralytics", "mediapipe", "transformers", "onnx", "tensorflow"):
            categories["Deep Learning & AI Vision"].append((pkg, spec))
        elif p_lower in ("fastapi", "uvicorn", "flask", "django", "requests", "httpx", "aiohttp", "starlette", "websockets"):
            categories["Web & Networking"].append((pkg, spec))
        else:
            categories["Other Utilities"].append((pkg, spec))

    return {k: v for k, v in categories.items() if v}


def generate_requirements_txt(categorized: Dict[str, List[Tuple[str, str]]], output_path: Path) -> None:
    """Write standard categorized requirements.txt file."""
    lines = [
        "# Auto-generated requirements.txt",
        "# ======================================================",
        "",
    ]
    for cat_name, pkgs in categorized.items():
        lines.append(f"# {cat_name}")
        for pkg, spec in sorted(pkgs):
            lines.append(f"{pkg}{spec}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Generated requirements.txt -> {output_path.resolve()}")


def generate_pyproject_toml(
    pkg_list: List[Tuple[str, str, bool]],
    project_name: str,
    output_path: Path,
) -> None:
    """Write standard PEP 621 pyproject.toml configuration."""
    main_deps = []
    dev_deps = []

    for pkg, spec, is_dev in sorted(pkg_list):
        line = f'    "{pkg}{spec}",'
        if is_dev:
            dev_deps.append(line)
        else:
            main_deps.append(line)

    lines = [
        '[build-system]',
        'requires = ["setuptools>=61.0"]',
        'build-backend = "setuptools.build_meta"',
        '',
        '[project]',
        f'name = "{project_name}"',
        'version = "1.0.0"',
        'description = "Auto-generated project specification"',
        'readme = "README.md"',
        'requires-python = ">=3.10"',
        'dependencies = [',
        *main_deps,
        ']',
        '',
        '[project.optional-dependencies]',
        'dev = [',
        *dev_deps,
        ']',
        '',
        '[tool.pytest.ini_options]',
        'testpaths = ["tests"]',
        'asyncio_mode = "strict"',
        '',
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ Generated pyproject.toml   -> {output_path.resolve()}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Auto Dependency & Requirements Generator using Python AST."
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default=".",
        help="Path to the target Python project root directory (default: current directory).",
    )
    parser.add_argument(
        "--exact",
        "-e",
        action="store_true",
        help="Use exact pinned versions (==X.Y.Z) instead of minimum constraints (>=X.Y.0).",
    )
    parser.add_argument(
        "--name",
        "-n",
        type=str,
        default=None,
        help="Project name for pyproject.toml (default: name of the project folder).",
    )

    args = parser.parse_args()
    root_path = Path(args.path).resolve()

    if not root_path.exists() or not root_path.is_dir():
        print(f"❌ Error: Path '{root_path}' does not exist or is not a directory.")
        sys.exit(1)

    project_name = args.name or root_path.name

    print("=" * 70)
    print("      🚀 Auto Dependency & Requirements Generator (AST Engine)     ")
    print("=" * 70)

    # 1. Scan and extract imports
    raw_modules = scan_project_imports(root_path)

    if not raw_modules:
        print("⚠️ No external third-party dependencies detected.")
        sys.exit(0)

    # 2. Resolve package names
    module_to_pkg = resolve_package_names(raw_modules)
    unique_packages = set(module_to_pkg.values())

    print(f"📦 Identified {len(unique_packages)} unique third-party packages:")
    for mod, pkg in sorted(module_to_pkg.items()):
        print(f"   • Import '{mod}' -> PyPI Package '{pkg}'")

    # 3. Resolve installed versions
    pkg_list = get_installed_versions(unique_packages, exact=args.exact)
    categorized = categorize_packages(pkg_list)

    # 4. Generate files
    req_file = root_path / "requirements.txt"
    pyproj_file = root_path / "pyproject.toml"

    print("\n📝 Generating project configuration files...")
    generate_requirements_txt(categorized, req_file)
    generate_pyproject_toml(pkg_list, project_name, pyproj_file)

    print("\n🎉 Done! Both dependency files are up to date and ready for production.")
    print("=" * 70)


if __name__ == "__main__":
    main()
