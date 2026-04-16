"""
tree_gen.py — Standalone Directory Structure Generator
=======================================================
Generates a Markdown-formatted directory tree from a given path.

Usage (CLI):
    python tree_gen.py /path/to/dir
    python tree_gen.py /path/to/dir --output /path/to/out --layout horizontal
    python tree_gen.py /path/to/dir --max-depth 3 --ignore-ext .log,.tmp
    python tree_gen.py /path/to/dir --ignore-path /path/to/skip,/another/path
    python tree_gen.py /path/to/dir --file-name my_structure

Usage (Import):
    from tree_gen import TreeGen

    result = TreeGen.run(
        input_path="/path/to/dir",
        output_path="/path/to/out",   # optional, defaults to input_path
        file_name="my_structure",     # optional
        layout="vertical",            # "vertical" | "horizontal"
        max_depth=4,                  # 0 = unlimited
        use_gitignore=True,
        ignored_path="/skip/this,/and/this",
        ignored_extensions=".log,.tmp",
    )
    print(result)
"""

import argparse
import fnmatch
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


class TreeGen:
    """
    Standalone directory tree generator. No external dependencies.

    All logic is in the class-level `run()` classmethod.
    Can also be used as a CLI tool (see module docstring).
    """

    # ── Default ignored patterns ───────────────────────────────────────────────
    IGNORED_PATTERNS: frozenset = frozenset({
        # Version control and IDE
        ".git", ".gitkeep", ".idea", ".vscode", ".DS_Store",
        # Python
        "__pycache__", ".pytest_cache", ".mypy_cache", ".tox", ".egg-info",
        ".pyc", ".pyo", ".pyd",
        # Node.js
        "node_modules", ".npm", "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
        # Build outputs
        "dist", "build", "coverage",
        # Lock files
        "poetry.lock", "Gemfile.lock", ".lock",
        # Environment
        ".env", ".venv",
        # Media files
        ".svg", ".png", ".jpg", ".jpeg", ".gif", ".bmp",
        ".tiff", ".ico", ".mp4", ".mp3",
        # Web assets
        ".html", ".css", ".woff", ".woff2", ".ttf", ".eot",
        # Binaries and archives
        ".so", ".dll", ".exe", ".bin", ".iso", ".tar", ".gz", ".zip",
        # Temp and log
        ".log", ".tmp", ".bak", ".swp", ".swo",
        # Other
        ".java",
    })

    MAX_NAME_LEN: int = 35

    # ── Gitignore helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _load_gitignore(root: Path) -> list[str]:
        gi = root / ".gitignore"
        if not gi.exists():
            return []
        return [
            line.strip()
            for line in gi.read_text(encoding="utf-8", errors="ignore").splitlines()
            if line.strip() and not line.startswith("#")
        ]

    @staticmethod
    def _matches_gitignore(name: str, patterns: list[str]) -> bool:
        return any(
            fnmatch.fnmatch(name, p) or fnmatch.fnmatch(name, p.lstrip("/"))
            for p in patterns
        )

    # ── Skip logic ─────────────────────────────────────────────────────────────

    @classmethod
    def _should_skip(
        cls,
        item: Path,
        effective_patterns: frozenset,
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
    ) -> bool:
        name = item.name

        # Never include the output file itself
        if name == output_filename and item.parent == target_root:
            return True

        # Exact name match
        if name in effective_patterns:
            return True

        # Extension match
        if any(item.name.endswith(pat) for pat in effective_patterns if pat.startswith(".")):
            return True

        # Hidden files / dirs (except whitelisted)
        if name.startswith(".") and name not in {".env.example", ".editorconfig"}:
            return True

        # User-supplied absolute exclusions
        try:
            resolved = str(item.resolve())
        except OSError:
            resolved = str(item.absolute())
        if resolved in extra_excludes:
            return True

        # .gitignore rules
        if use_gitignore and cls._matches_gitignore(name, gitignore_patterns):
            return True

        return False

    @classmethod
    def _get_children(
        cls,
        dir_path: Path,
        effective_patterns: frozenset,
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
    ) -> list:
        try:
            items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except (PermissionError, FileNotFoundError):
            return []
        return [
            item for item in items
            if not cls._should_skip(
                item, effective_patterns, extra_excludes,
                gitignore_patterns, use_gitignore, output_filename, target_root,
            )
        ]

    # ── Statistics ─────────────────────────────────────────────────────────────

    @dataclass
    class Stats:
        files: int = 0
        dirs: int = 0
        total_bytes: int = 0

    @staticmethod
    def _fmt_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    @classmethod
    def _collect_stats(
        cls, dir_path: Path, stats, effective_patterns,
        extra_excludes, gitignore_patterns, use_gitignore, output_filename, target_root,
    ) -> None:
        for item in cls._get_children(
            dir_path, effective_patterns, extra_excludes,
            gitignore_patterns, use_gitignore, output_filename, target_root,
        ):
            if item.is_dir():
                stats.dirs += 1
                cls._collect_stats(
                    item, stats, effective_patterns, extra_excludes,
                    gitignore_patterns, use_gitignore, output_filename, target_root,
                )
            else:
                stats.files += 1
                try:
                    stats.total_bytes += item.stat().st_size
                except OSError:
                    pass

    # ── Vertical renderer ──────────────────────────────────────────────────────

    @classmethod
    def _render_vertical(
        cls, dir_path: Path, effective_patterns, extra_excludes,
        gitignore_patterns, use_gitignore, output_filename, target_root,
        max_depth: int, prefix: str = "", current_depth: int = 0,
    ) -> list:
        if max_depth and current_depth >= max_depth:
            return []

        children = cls._get_children(
            dir_path, effective_patterns, extra_excludes,
            gitignore_patterns, use_gitignore, output_filename, target_root,
        )
        lines = []
        for i, item in enumerate(children):
            is_last = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            name = item.name
            display = (name[:cls.MAX_NAME_LEN - 2] + "..") if len(name) > cls.MAX_NAME_LEN else name
            lines.append(f"{prefix}{connector}{display}")

            if item.is_dir():
                extension = "    " if is_last else "│   "
                lines.extend(cls._render_vertical(
                    item, effective_patterns, extra_excludes,
                    gitignore_patterns, use_gitignore, output_filename, target_root,
                    max_depth, prefix + extension, current_depth + 1,
                ))
        return lines

    # ── Horizontal renderer ────────────────────────────────────────────────────

    @classmethod
    def _render_horizontal(
        cls, children: list, effective_patterns, extra_excludes,
        gitignore_patterns, use_gitignore, output_filename, target_root, max_depth: int,
    ) -> list:
        if not children:
            return []

        all_trees = []
        for child in children:
            sub = (
                cls._render_vertical(
                    child, effective_patterns, extra_excludes,
                    gitignore_patterns, use_gitignore, output_filename, target_root,
                    max_depth, "", 0,
                )
                if child.is_dir() else []
            )
            all_trees.append(["│"] + sub)

        col_widths = [
            max(max((len(l) for l in tree), default=0), len(child.name)) + 2
            for child, tree in zip(children, all_trees)
        ]
        spacing = 3
        col_starts: list = []
        pos = 0
        for w in col_widths:
            col_starts.append(pos)
            pos += w + spacing
        total_width = pos - spacing

        col_centers = [col_starts[i] + col_widths[i] // 2 for i in range(len(children))]
        output_lines: list = []

        # Top connector
        h_line = [" "] * total_width
        fc, lc = col_centers[0], col_centers[-1]
        for i in range(fc, lc + 1):
            h_line[i] = "─"
        h_line[fc] = "┌" if len(children) > 1 else "│"
        if len(children) > 1:
            h_line[lc] = "┐"
        for center in col_centers[1:-1]:
            h_line[center] = "┬"
        output_lines.append("".join(h_line))

        v_line = [" "] * total_width
        for center in col_centers:
            v_line[center] = "│"
        output_lines.append("".join(v_line))

        name_line = [" "] * total_width
        for idx, child in enumerate(children):
            name = child.name
            start = col_centers[idx] - len(name) // 2
            for j, ch in enumerate(name):
                p = start + j
                if 0 <= p < total_width:
                    name_line[p] = ch
        output_lines.append("".join(name_line))

        max_height = max(len(t) for t in all_trees)
        for row in range(max_height):
            row_chars = [" "] * total_width
            for col_idx, tree in enumerate(all_trees):
                if row < len(tree):
                    content = tree[row]
                    if content == "│":
                        p = col_centers[col_idx]
                        if 0 <= p < total_width:
                            row_chars[p] = "│"
                    else:
                        start_pos = col_starts[col_idx]
                        for j, ch in enumerate(content):
                            p = start_pos + j
                            if 0 <= p < total_width:
                                row_chars[p] = ch
            output_lines.append("".join(row_chars).rstrip())

        return output_lines

    # ── Public entry point ─────────────────────────────────────────────────────

    @classmethod
    def run(
        cls,
        input_path: str,
        output_path: Optional[str] = None,
        file_name: Optional[str] = None,
        layout: str = "vertical",
        max_depth: int = 4,
        use_gitignore: bool = True,
        ignored_path: str = "",
        ignored_extensions: str = "",
    ) -> str:
        """
        Generate a Markdown directory tree and write it to a file.

        Returns a human-readable summary string (success or error message).
        """
        # ── Resolve paths ────────────────────────────────────────────────────
        input_path_str = input_path.strip()
        if not input_path_str:
            return "Error: `input_path` is required."

        src = Path(input_path_str).resolve()
        dst = Path(output_path.strip()).resolve() if output_path else src

        if not src.exists() or not src.is_dir():
            return f"Error: '{input_path_str}' does not exist or is not a directory."

        # ── Build exclusion sets ─────────────────────────────────────────────
        extra_excludes: set[str] = set()
        for p in (ignored_path or "").split(","):
            p = p.strip()
            if p:
                try:
                    extra_excludes.add(str(Path(p).resolve()))
                except Exception:
                    extra_excludes.add(p)

        extra_ext: set[str] = set()
        for ext in (ignored_extensions or "").split(","):
            ext = ext.strip().lower()
            if ext:
                extra_ext.add(ext if ext.startswith(".") else f".{ext}")

        effective_patterns = cls.IGNORED_PATTERNS | extra_ext

        # ── Gitignore ────────────────────────────────────────────────────────
        gitignore_patterns: list[str] = cls._load_gitignore(src) if use_gitignore else []

        # ── Output filename ──────────────────────────────────────────────────
        if file_name:
            fn = file_name.strip()
            output_filename = fn if fn.endswith(".md") else f"{fn}.md"
        else:
            output_filename = f"{src.name}_structure.md"

        output_file = dst / output_filename

        # ── Render ───────────────────────────────────────────────────────────
        try:
            if layout == "horizontal":
                top_children = cls._get_children(
                    src, effective_patterns, extra_excludes,
                    gitignore_patterns, use_gitignore, output_filename, src,
                )
                tree_lines = cls._render_horizontal(
                    top_children, effective_patterns, extra_excludes,
                    gitignore_patterns, use_gitignore, output_filename, src, max_depth,
                )
            else:
                tree_lines = cls._render_vertical(
                    src, effective_patterns, extra_excludes,
                    gitignore_patterns, use_gitignore, output_filename, src, max_depth,
                )

            dst.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# Directory Structure: {src.name}/\n")
                f.write(f"## Path: {src}\n\n")
                f.write(f"{src.name}/\n│\n")
                for line in tree_lines:
                    f.write(line + "\n")

        except Exception as e:
            return f"Error: {e}"

        # ── Stats ────────────────────────────────────────────────────────────
        stats = cls.Stats()
        cls._collect_stats(
            src, stats, effective_patterns, extra_excludes,
            gitignore_patterns, use_gitignore, output_filename, src,
        )
        line_count = len(tree_lines) + 4
        size_bytes = output_file.stat().st_size if output_file.exists() else 0
        depth_note = "unlimited" if max_depth == 0 else f"{max_depth} levels"

        summary = "\n".join([
            "✅ Directory Structure Generated.",
            f"   Path    : {output_file}",
            f"   Layout  : {layout}",
            f"   Depth   : {depth_note}",
            f"   Lines   : {line_count}",
            f"   Size    : {cls._fmt_bytes(size_bytes)}",
            f"   Dirs    : {stats.dirs}",
            f"   Files   : {stats.files}",
            f"   Scanned : {cls._fmt_bytes(stats.total_bytes)}",
        ])

        if line_count > 500:
            summary += (
                f"\n\n   ⚠️  Tip: Output is {line_count} lines. "
                "Consider reducing --max-depth or adding --ignore-path entries."
            )

        return summary


# ── CLI entry point ────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="tree_gen",
        description="Generate a Markdown-formatted directory structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input_path",           help="Directory to scan (required)")
    p.add_argument("--output",             dest="output_path",      default=None,       help="Directory to write the .md file (default: same as input)")
    p.add_argument("--file-name",          dest="file_name",        default=None,       help="Output filename without extension (default: <dir_name>_structure)")
    p.add_argument("--layout",             dest="layout",           default="vertical", choices=["vertical", "horizontal"], help="Tree layout style (default: vertical)")
    p.add_argument("--max-depth",          dest="max_depth",        default=4, type=int, help="Max recursion depth; 0 = unlimited (default: 4)")
    p.add_argument("--no-gitignore",       dest="use_gitignore",    action="store_false", help="Disable .gitignore parsing")
    p.add_argument("--ignore-path",        dest="ignored_path",     default="",         help="Comma-separated absolute paths to exclude")
    p.add_argument("--ignore-ext",         dest="ignored_extensions", default="",       help="Comma-separated file extensions to exclude (e.g. .log,.tmp)")
    return p


if __name__ == "__main__":
    args = _build_parser().parse_args()
    result = TreeGen.run(
        input_path=args.input_path,
        output_path=args.output_path,
        file_name=args.file_name,
        layout=args.layout,
        max_depth=args.max_depth,
        use_gitignore=args.use_gitignore,
        ignored_path=args.ignored_path,
        ignored_extensions=args.ignored_extensions,
    )
    print(result)
    sys.exit(0 if result.startswith("✅") else 1)
