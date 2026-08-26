import ast
import fnmatch
import importlib.metadata
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from helpers.tool import Tool, Response

_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR.parent.parent
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))


# ── Constants & Mappings ──────────────────────────────────────────────────────

# Known namespace packages where the top 2 (or 3) dotted segments define the package
KNOWN_NAMESPACE_PREFIXES: Set[str] = {
    "google",
    "azure",
    "opentelemetry",
    "oslo",
    "backports",
    "zope",
    "ruamel",
    "jaraco",
}

# Common import-to-PyPI package mapping for libraries where import != package name
KNOWN_PACKAGE_MAP: Dict[str, str] = {
    # AI, LLM & GenAI
    "google.generativeai": "google-generativeai",
    "google.ai.generativelanguage": "google-ai-generativelanguage",
    "google.cloud.storage": "google-cloud-storage",
    "google.cloud.firestore": "google-cloud-firestore",
    "google.cloud.bigquery": "google-cloud-bigquery",
    "anthropic": "anthropic",
    "openai": "openai",
    "langchain_core": "langchain-core",
    "langchain_community": "langchain-community",
    "langchain_openai": "langchain-openai",
    "langchain_anthropic": "langchain-anthropic",
    "openevolve": "openevolve",
    # Computer Vision, Documents & Media
    "cv2": "opencv-python",
    "PIL": "pillow",
    "fitz": "pymupdf",
    "docx": "python-docx",
    "pptx": "python-pptx",
    "pdf2image": "pdf2image",
    "pdfplumber": "pdfplumber",
    "pypdf": "pypdf",
    "skimage": "scikit-image",
    "openpyxl": "openpyxl",
    # Data Science & Core Math
    "sklearn": "scikit-learn",
    "yaml": "pyyaml",
    "bs4": "beautifulsoup4",
    "dateutil": "python-dateutil",
    "magic": "python-magic",
    "attr": "attrs",
    "attrs": "attrs",
    "markdown_it": "markdown-it-py",
    "markupsafe": "markupsafe",
    # Web, Networking & Config
    "pydantic_settings": "pydantic-settings",
    "dotenv": "python-dotenv",
    "jose": "python-jose",
    "multipart": "python-multipart",
    "jwt": "pyjwt",
    "websocket": "websocket-client",
    "serial": "pyserial",
    "faster_whisper": "faster-whisper",
    "psycopg2": "psycopg2-binary",
    "asyncpg": "asyncpg",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "tenacity": "tenacity",
    "redis": "redis",
    "celery": "celery",
    "pytest_asyncio": "pytest-asyncio",
    "pytest_cov": "pytest-cov",
    "pytest_mock": "pytest-mock",
}

# Truly universal build/cache/vcs directories to ignore during scan
UNIVERSAL_IGNORED_DIRS: Set[str] = {
    ".git",
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    ".eggs",
    "*.egg-info",
    ".tox",
    ".coverage",
    "htmlcov",
    ".idea",
    ".vscode",
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
        "by scanning Python source code using AST. Resolves PyPI names, handles namespaces, "
        "and checks project virtualenv for exact installed versions."
    )
    arguments: dict = {
        "path": "Target Python project root directory to scan (e.g. '/path/to/project'). Defaults to current directory.",
        "exact": "Optional boolean ('true' or 'false'). If true, uses exact pinned versions (==X.Y.Z) instead of minimum constraints (>=X.Y.0). Default: false.",
        "name": "Optional project name for pyproject.toml. Defaults to project folder name.",
        "output_dir": "Optional output directory where requirement files will be written. Defaults to the scanned path.",
        "format": "Optional output format: 'both' (default), 'requirements' (only requirements.txt), or 'pyproject' (only pyproject.toml).",
        "ignored_dirs": "Optional comma-separated list of additional directories to ignore during scan (e.g. 'tests,docs,demo')."
    }
    instruction: str = "For Skill instruction run human-skills --skill_info gen-requirements"

    # ── Gitignore & Ignore Helpers ─────────────────────────────────────────────

    @staticmethod
    def _load_gitignore_patterns(root: Path) -> List[str]:
        """Read .gitignore from root and return valid pattern lines."""
        gi_path = root / ".gitignore"
        if not gi_path.exists():
            return []
        patterns = []
        try:
            for line in gi_path.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
        except Exception:
            pass
        return patterns

    @staticmethod
    def _is_ignored(dir_name: str, rel_path_str: str, custom_ignores: Set[str], gitignore_patterns: List[str]) -> bool:
        """Check if a directory should be skipped."""
        if dir_name in UNIVERSAL_IGNORED_DIRS or dir_name.startswith("."):
            return True
        if dir_name in custom_ignores:
            return True
        for pattern in gitignore_patterns:
            pat = pattern.rstrip("/")
            if fnmatch.fnmatch(dir_name, pat) or fnmatch.fnmatch(rel_path_str, pat):
                return True
        return False

    # ── Stdlib & Local Module Discovery ────────────────────────────────────────

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
    def _discover_local_modules(project_root: Path, custom_ignores: Set[str]) -> Set[str]:
        """
        Comprehensive discovery of all local package names and module roots.
        Supports standard root layout, src/ layout, app/ layout, and nested packages.
        """
        local_names: Set[str] = set()

        search_roots = [project_root]
        # Support src/ and app/ layouts
        for sub in ("src", "app", "lib"):
            sub_path = project_root / sub
            if sub_path.is_dir():
                search_roots.append(sub_path)
                local_names.add(sub)

        for base in search_roots:
            try:
                for item in base.iterdir():
                    if item.name.startswith(".") or item.name in UNIVERSAL_IGNORED_DIRS or item.name in custom_ignores:
                        continue
                    if item.is_dir():
                        # Any folder with a .py file anywhere inside is considered a local package/submodule
                        has_py = any(item.glob("*.py")) or any(item.glob("**/*.py"))
                        if has_py:
                            local_names.add(item.name)
                    elif item.suffix == ".py":
                        local_names.add(item.stem)
            except Exception:
                pass

        return local_names

    # ── AST Import Extraction ──────────────────────────────────────────────────

    @staticmethod
    def _extract_imports_from_file(file_path: Path) -> Tuple[Set[str], Optional[str]]:
        """
        Parse a Python file using AST and extract candidate module names.
        Intelligently preserves namespace prefixes (e.g. google.generativeai, azure.storage).
        """
        imported_modules: Set[str] = set()
        error_msg: Optional[str] = None

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(content, filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        parts = alias.name.split(".")
                        if parts:
                            top = parts[0]
                            # Check namespace candidates
                            if len(parts) >= 2 and (top in KNOWN_NAMESPACE_PREFIXES or f"{parts[0]}.{parts[1]}" in KNOWN_PACKAGE_MAP):
                                imported_modules.add(f"{parts[0]}.{parts[1]}")
                            elif len(parts) >= 3 and top in KNOWN_NAMESPACE_PREFIXES:
                                imported_modules.add(f"{parts[0]}.{parts[1]}.{parts[2]}")
                            else:
                                imported_modules.add(top)

                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.level == 0:  # Absolute imports only
                        parts = node.module.split(".")
                        if parts:
                            top = parts[0]
                            if len(parts) >= 2 and (top in KNOWN_NAMESPACE_PREFIXES or f"{parts[0]}.{parts[1]}" in KNOWN_PACKAGE_MAP):
                                imported_modules.add(f"{parts[0]}.{parts[1]}")
                            elif len(parts) >= 3 and top in KNOWN_NAMESPACE_PREFIXES:
                                imported_modules.add(f"{parts[0]}.{parts[1]}.{parts[2]}")
                            else:
                                imported_modules.add(top)

        except Exception as e:
            error_msg = f"{file_path.name}: {str(e)}"

        return imported_modules, error_msg

    def _scan_project_imports(
        self, project_root: Path, custom_ignores: Set[str]
    ) -> Tuple[Set[str], int, List[str]]:
        """
        Scan all Python files across the project directory with comprehensive filtering.
        Returns (third_party_modules, scanned_files_count, failed_files_list).
        """
        all_imports: Set[str] = set()
        stdlib = self._get_stdlib_modules()
        local_mods = self._discover_local_modules(project_root, custom_ignores)
        gitignore_patterns = self._load_gitignore_patterns(project_root)

        count_files = 0
        failed_files: List[str] = []

        for root_dir, dirs, files in os.walk(project_root):
            curr_path = Path(root_dir)
            rel_path = curr_path.relative_to(project_root)

            # Filter out ignored directories
            dirs[:] = [
                d for d in dirs
                if not self._is_ignored(
                    d,
                    str((rel_path / d).as_posix()),
                    custom_ignores,
                    gitignore_patterns
                )
            ]

            for file in files:
                if file.endswith(".py"):
                    f_path = curr_path / file
                    count_files += 1
                    file_imports, err = self._extract_imports_from_file(f_path)
                    if err:
                        failed_files.append(err)
                    all_imports.update(file_imports)

        # Filter out standard library, local project modules, and private names
        third_party: Set[str] = set()
        for m in all_imports:
            top_part = m.split(".")[0]
            if top_part not in stdlib and top_part not in local_mods and not m.startswith("_"):
                third_party.add(m)

        return third_party, count_files, failed_files

    # ── PyPI Name & Virtualenv Resolution ─────────────────────────────────────

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
                # Handle dotted subpackages fallback
                clean_name = mod.replace("_", "-").replace(".", "-")
                resolved[mod] = clean_name
        return resolved

    @staticmethod
    def _find_project_venv(project_root: Path) -> Optional[Path]:
        """Detect virtual environment (.venv, venv, env) inside project_root."""
        for candidate_name in (".venv", "venv", "env"):
            candidate = project_root / candidate_name
            if candidate.is_dir():
                # Check for standard venv indicators
                has_cfg = (candidate / "pyvenv.cfg").exists()
                has_bin = (candidate / "bin" / "python").exists() or (candidate / "Scripts" / "python.exe").exists()
                if has_cfg or has_bin:
                    return candidate
        return None

    @staticmethod
    def _query_venv_packages(venv_path: Path) -> Dict[str, str]:
        """
        Query target project's venv using pip list JSON output.
        Returns {canonical_package_name_lower: version_string}.
        """
        python_bin = venv_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if not python_bin.exists():
            return {}

        try:
            res = subprocess.run(
                [str(python_bin), "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
                timeout=15
            )
            data = json.loads(res.stdout)
            return {item["name"].lower().replace("_", "-"): item["version"] for item in data}
        except Exception:
            # Fallback to pip freeze
            try:
                res = subprocess.run(
                    [str(python_bin), "-m", "pip", "freeze"],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=15
                )
                freeze_map = {}
                for line in res.stdout.splitlines():
                    if "==" in line:
                        name, _, ver = line.partition("==")
                        freeze_map[name.strip().lower().replace("_", "-")] = ver.strip()
                return freeze_map
            except Exception:
                return {}

    def _get_package_versions(
        self,
        packages: Set[str],
        project_root: Path,
        exact: bool = False,
    ) -> Tuple[List[Tuple[str, str, bool]], Optional[str], List[str]]:
        """
        Resolve versions for discovered packages.
        Prioritizes target project venv, then falls back to host environment.
        Returns (pkg_list, venv_status_msg, unversioned_packages).
        """
        venv_path = self._find_project_venv(project_root)
        venv_pkgs: Dict[str, str] = {}
        venv_status_msg: Optional[str] = None

        if venv_path:
            venv_pkgs = self._query_venv_packages(venv_path)
            venv_status_msg = f"Virtual environment detected at: {venv_path.relative_to(project_root)}"
        else:
            venv_status_msg = "⚠️ No virtual environment (.venv/venv/env) found in project; using host environment."

        results: List[Tuple[str, str, bool]] = []
        unversioned_packages: List[str] = []

        for pkg in sorted(packages):
            is_dev = pkg.lower() in DEV_PACKAGES
            normalized_name = pkg.lower().replace("_", "-")
            installed_ver = None

            # 1. Check target project venv first
            if normalized_name in venv_pkgs:
                installed_ver = venv_pkgs[normalized_name]

            # 2. Fallback to host environment
            if not installed_ver:
                try:
                    installed_ver = importlib.metadata.version(pkg)
                except Exception:
                    try:
                        installed_ver = importlib.metadata.version(normalized_name)
                    except Exception:
                        pass

            if installed_ver:
                if exact:
                    spec = f"=={installed_ver}"
                else:
                    parts = installed_ver.split(".")
                    if len(parts) >= 2:
                        min_ver = f"{parts[0]}.{parts[1]}.0"
                    else:
                        min_ver = f"{parts[0]}.0"
                    spec = f">={min_ver}"
            else:
                spec = ""
                unversioned_packages.append(pkg)

            results.append((pkg, spec, is_dev))

        return results, venv_status_msg, unversioned_packages

    # ── Formatting & File Generation ───────────────────────────────────────────

    @staticmethod
    def _categorize_packages(pkg_list: List[Tuple[str, str, bool]]) -> Dict[str, List[Tuple[str, str]]]:
        """Organize packages into clean functional categories."""
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
            elif p_lower in (
                "torch", "torchvision", "torchaudio", "ultralytics", "mediapipe",
                "transformers", "onnx", "tensorflow", "openai", "anthropic",
                "google-generativeai", "google-ai-generativelanguage", "langchain",
                "langchain-core", "langchain-community", "openevolve"
            ):
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
            "# Auto-generated requirements.txt by human-skills (gen_requirements)",
            "# ==================================================================",
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

        # Parse user-supplied custom ignores
        custom_ignores_str = self.args.get("ignored_dirs", "")
        custom_ignores = {
            s.strip() for s in custom_ignores_str.split(",") if s.strip()
        }

        # 1. Scan and extract imports
        raw_modules, scanned_files, failed_files = self._scan_project_imports(project_root, custom_ignores)

        if not raw_modules:
            return Response(
                message=(
                    f"⚠️ No external third-party dependencies detected in {project_root}.\n"
                    f"   • Scanned {scanned_files} Python source files."
                ),
                break_loop=False,
            )

        # 2. Resolve package names & namespaces
        module_to_pkg = self._resolve_package_names(raw_modules)
        unique_packages = set(module_to_pkg.values())

        # 3. Resolve installed versions (Prioritizing target project venv)
        pkg_list, venv_status, unversioned = self._get_package_versions(
            unique_packages, project_root, exact=exact
        )
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
            f"   Venv      : {venv_status}",
            f"   Outputs   : {', '.join(Path(f).name for f in created_files)} in {out_dir}",
            "",
            "📦 Discovered Dependencies:",
        ]

        for cat_name, pkgs in categorized.items():
            msg_lines.append(f"   [{cat_name}]")
            for pkg, spec in sorted(pkgs):
                msg_lines.append(f"     • {pkg}{spec}")

        if unversioned:
            msg_lines.append("")
            msg_lines.append(f"ℹ️ {len(unversioned)} packages not currently installed in venv/host (generated without version constraint):")
            msg_lines.append(f"   {', '.join(sorted(unversioned))}")

        if failed_files:
            msg_lines.append("")
            msg_lines.append(f"⚠️ {len(failed_files)} file(s) failed parsing:")
            for err in failed_files[:5]:
                msg_lines.append(f"   • {err}")
            if len(failed_files) > 5:
                msg_lines.append(f"   ... and {len(failed_files) - 5} more")

        return Response(message="\n".join(msg_lines), break_loop=False)
