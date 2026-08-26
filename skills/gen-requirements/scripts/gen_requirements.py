import ast
import fnmatch
import importlib.metadata
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from helpers.tool import Tool, Response

_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR.parent.parent
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))


# ── Constants & Mappings ──────────────────────────────────────────────────────

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
    "google.generativeai": "google-generativeai",
    "anthropic": "anthropic",
    "openai": "openai",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "tenacity": "tenacity",
    "redis": "redis",
    "celery": "celery",
    "asyncpg": "asyncpg",
    "psycopg2": "psycopg2-binary",
}

# Directories to always ignore when scanning
DEFAULT_IGNORED_DIRS: Set[str] = {
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
    "site-packages",
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
    "pre-commit",
    "httpx",
}


class GenerateRequirements(Tool):
    """
    Auto Dependency & Requirements Generator using Python AST.
    Recursively scans any Python project, filters stdlib and local imports,
    resolves PyPI distribution names and versions, and outputs standard
    requirements.txt and PEP 621 pyproject.toml.
    """
    name: str = "gen_requirements"
    description: str = (
        "Auto-generates clean, categorized requirements.txt and pyproject.toml "
        "by scanning Python source code using AST. Resolves PyPI names and installed versions."
    )
    arguments: dict = {
        "path": "Target Python project root directory to scan (e.g. '/path/to/project'). Defaults to current directory.",
        "exact": "Optional boolean ('true' or 'false'). If true, uses exact pinned versions (==X.Y.Z) instead of minimum constraints (>=X.Y.0). Default: false.",
        "name": "Optional project name for pyproject.toml. Defaults to project folder name.",
        "output_dir": "Optional output directory where requirement files will be written. Defaults to the scanned path.",
        "format": "Optional output format: 'both' (default), 'requirements' (only requirements.txt), or 'pyproject' (only pyproject.toml)."
    }
    instruction: str = "For Skill instruction run human-skills --skill_info gen-requirements"

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _get_stdlib_modules() -> Set[str]:
        """Retrieve all Python standard library module names."""
        if hasattr(sys, "stdlib_module_names"):
            return set(sys.stdlib_module_names)
        try:
            import distutils.sysconfig
            stdlib_dir = distutils.sysconfig.get_python_lib(standard_lib=True)
            names = set()
            for item in os.listdir(stdlib_dir):
                if item.endswith(".py"):
                    names.add(item[:-3])
                elif os.path.isdir(os.path.join(stdlib_dir, item)):
                    names.add(item)
            return names
        except Exception:
            return set()

    @staticmethod
    def _discover_local_modules(project_root: Path, ignored_dirs: Set[str]) -> Set[str]:
        """Identify local package directories and root python scripts so they aren't marked as third-party."""
        local_names: Set[str] = set()
        for item in project_root.iterdir():
            if item.name.startswith(".") or item.name in ignored_dirs:
                continue
            if item.is_dir():
                # Any dir with a .py file or __init__.py is a local package/module
                has_py = any(f.suffix == ".py" for f in item.rglob("*.py"))
                if has_py:
                    local_names.add(item.name)
            elif item.suffix == ".py":
                local_names.add(item.stem)
        return local_names

    @staticmethod
    def _extract_imports_from_file(file_path: Path) -> Set[str]:
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
        except Exception:
            pass
        return imported_modules

    def _scan_project_imports(self, project_root: Path) -> Tuple[Set[str], int]:
        """Scan all Python files across the project directory."""
        all_imports: Set[str] = set()
        stdlib = self._get_stdlib_modules()
        local_mods = self._discover_local_modules(project_root, DEFAULT_IGNORED_DIRS)

        count_files = 0
        for root_dir, dirs, files in os.walk(project_root):
            dirs[:] = [d for d in dirs if d not in DEFAULT_IGNORED_DIRS and not d.startswith(".")]
            for file in files:
                if file.endswith(".py"):
                    count_files += 1
                    f_path = Path(root_dir) / file
                    file_imports = self._extract_imports_from_file(f_path)
                    all_imports.update(file_imports)

        # Filter out standard library and local project modules
        third_party = {
            m for m in all_imports
            if m not in stdlib and m not in local_mods and not m.startswith("_")
        }
        return third_party, count_files

    @staticmethod
    def _resolve_package_names(raw_modules: Set[str]) -> Dict[str, str]:
        """Map raw module import names to actual PyPI package distribution names."""
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
                resolved[mod] = pkg_dist_map[mod][0]
            else:
                clean_name = mod.replace("_", "-")
                resolved[mod] = clean_name
        return resolved

    @staticmethod
    def _get_installed_versions(packages: Set[str], exact: bool = False) -> List[Tuple[str, str, bool]]:
        """Query current environment for package versions. Returns (pkg, version_spec, is_dev)."""
        results = []
        for pkg in sorted(packages):
            is_dev = pkg.lower() in DEV_PACKAGES
            try:
                installed_ver = importlib.metadata.version(pkg)
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
                spec = ""

            results.append((pkg, spec, is_dev))
        return results

    @staticmethod
    def _categorize_packages(pkg_list: List[Tuple[str, str, bool]]) -> Dict[str, List[Tuple[str, str]]]:
        """Organize packages into functional categories."""
        categories: Dict[str, List[Tuple[str, str]]] = {
            "Core Numerical & Math": [],
            "Configuration & Schemas": [],
            "Deep Learning & AI Vision": [],
            "Web & Networking": [],
            "Database & Storage": [],
            "Development & Testing": [],
            "Other Utilities": [],
        }

        for pkg, spec, is_dev in pkg_list:
            p_lower = pkg.lower()
            if is_dev:
                categories["Development & Testing"].append((pkg, spec))
            elif p_lower in ("numpy", "scipy", "pandas", "polars", "opencv-python", "pillow"):
                categories["Core Numerical & Math"].append((pkg, spec))
            elif p_lower in ("pydantic", "pydantic-settings", "python-dotenv", "pyyaml", "dynaconf", "tomli"):
                categories["Configuration & Schemas"].append((pkg, spec))
            elif p_lower in ("torch", "torchvision", "torchaudio", "ultralytics", "mediapipe", "transformers", "onnx", "tensorflow", "openai", "anthropic", "google-generativeai"):
                categories["Deep Learning & AI Vision"].append((pkg, spec))
            elif p_lower in ("fastapi", "uvicorn", "flask", "django", "requests", "httpx", "aiohttp", "starlette", "websockets", "websocket-client"):
                categories["Web & Networking"].append((pkg, spec))
            elif p_lower in ("sqlalchemy", "alembic", "asyncpg", "psycopg2", "psycopg2-binary", "pymongo", "redis", "aioredis"):
                categories["Database & Storage"].append((pkg, spec))
            else:
                categories["Other Utilities"].append((pkg, spec))

        return {k: v for k, v in categories.items() if v}

    @staticmethod
    def _generate_requirements_txt(categorized: Dict[str, List[Tuple[str, str]]], output_path: Path) -> None:
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

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _generate_pyproject_toml(
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

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding="utf-8")

    # ── Execute ───────────────────────────────────────────────────────────────

    async def execute(self, **kwargs) -> Response:
        path_str = self.args.get("path", ".")
        project_root = Path(path_str).resolve()

        if not project_root.exists() or not project_root.is_dir():
            return Response(
                message=f"❌ Error: Path '{project_root}' does not exist or is not a directory.",
                break_loop=False,
            )

        exact_str = str(self.args.get("exact", "false")).lower()
        exact = exact_str in ("true", "1", "yes", "y")

        project_name = self.args.get("name") or project_root.name
        out_dir_str = self.args.get("output_dir")
        out_dir = Path(out_dir_str).resolve() if out_dir_str else project_root
        out_dir.mkdir(parents=True, exist_ok=True)

        fmt = str(self.args.get("format", "both")).lower()

        # 1. Scan and extract imports
        raw_modules, scanned_files = self._scan_project_imports(project_root)

        if not raw_modules:
            return Response(
                message=(
                    f"⚠️ No external third-party dependencies detected in {project_root}.\n"
                    f"   • Scanned {scanned_files} Python source files."
                ),
                break_loop=False,
            )

        # 2. Resolve package names
        module_to_pkg = self._resolve_package_names(raw_modules)
        unique_packages = set(module_to_pkg.values())

        # 3. Resolve installed versions
        pkg_list = self._get_installed_versions(unique_packages, exact=exact)
        categorized = self._categorize_packages(pkg_list)

        # 4. Generate files
        created_files = []
        if fmt in ("both", "requirements"):
            req_file = out_dir / "requirements.txt"
            self._generate_requirements_txt(categorized, req_file)
            created_files.append(str(req_file))

        if fmt in ("both", "pyproject"):
            pyproj_file = out_dir / "pyproject.toml"
            self._generate_pyproject_toml(pkg_list, project_name, pyproj_file)
            created_files.append(str(pyproj_file))

        # Build response message
        msg_lines = [
            "✅ Dependency Generation Completed Successfully!",
            f"   Project   : {project_name}",
            f"   Scanned   : {scanned_files} Python source files",
            f"   Packages  : {len(unique_packages)} third-party dependencies detected",
            f"   Mode      : {'Exact pinned (==)' if exact else 'Minimum constraint (>=)'}",
            f"   Outputs   : {', '.join(Path(f).name for f in created_files)} in {out_dir}",
            "",
            "📦 Discovered Dependencies:",
        ]

        for cat_name, pkgs in categorized.items():
            msg_lines.append(f"   [{cat_name}]")
            for pkg, spec in sorted(pkgs):
                msg_lines.append(f"     • {pkg}{spec}")

        return Response(message="\n".join(msg_lines), break_loop=False)
