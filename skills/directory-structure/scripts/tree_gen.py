import sys
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from helpers.tool import Tool, Response

_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR.parent.parent
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))



class TreeGen(Tool):
    """
    Generate a directory structure in Markdown format using professional
    ASCII branch connectors (├──, └──, │).

    Args:
        input_path        : Directory to scan. (REQUIRED)
        output_path       : Directory to write the structure file.
                            Defaults to input_path.
        file_name         : Custom output filename.
                            Defaults to {dir_name}_structure.md.
        layout            : "vertical" (default) or "horizontal".
        max_depth         : Maximum depth to recurse. Default: 4.
                            Set to 0 for unlimited depth.
        use_gitignore     : Parse .gitignore in input_path and apply rules.
                            Default: true.
        ignored_path      : Comma-separated absolute paths to exclude.
        ignored_extensions: Comma-separated extensions to exclude
                            (e.g. ".log,.tmp").
    """

    # Default ignored patterns (common build artifacts, dependencies, and media files)
    IGNORED_PATTERNS: frozenset = frozenset({
        # Version control and IDE
        ".git", ".gitkeep", ".idea",
        ".vscode", ".DS_Store",

        # Python
        "__pycache__", ".pytest_cache",
        ".mypy_cache", ".tox", ".egg-info",
        ".pyc", ".pyo", ".pyd",

        # Node.js
        "node_modules", ".npm", "package-lock.json",
        "yarn.lock", "pnpm-lock.yaml",

        # Build outputs
        "dist", "build", "coverage",

        # Lock files
        "poetry.lock", "Gemfile.lock", ".lock",

        # Environment files
        ".env", ".venv",

        # Media files
        ".svg", ".png", ".jpg",
        ".jpeg", ".gif", ".bmp",
        ".tiff", ".ico", ".mp4", ".mp3",

        # Web assets
        ".html", ".css", ".woff", ".woff2", ".ttf", ".eot",

        # Binaries and archives
        ".so", ".dll", ".exe", ".bin", ".iso", ".tar", ".gz", ".zip",

        # Temporary and log files
        ".log", ".tmp", ".bak", ".swp", ".swo",

        # Other
        ".java",
    })

    # Maximum characters for a filename before truncation
    MAX_NAME_LEN: int = 35

    # ── Gitignore helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _load_gitignore_patterns(root: Path) -> list[str]:
        """Read .gitignore from root and return non-comment, non-empty lines."""
        gi_path = root / ".gitignore"
        if not gi_path.exists():
            return []
        patterns = []
        for line in gi_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
        return patterns

    @staticmethod
    def _matches_gitignore(name: str, patterns: list[str]) -> bool:
        """Return True if name matches any gitignore pattern."""
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
            if fnmatch.fnmatch(name, pattern.lstrip("/")):
                return True
        return False

    # ── Skip logic ────────────────────────────────────────────────────────────

    def _should_skip(
        self,
        item: Path,
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
    ) -> bool:
        """Return True if this item should be excluded from the tree."""
        name = item.name

        # Always skip the output file itself
        if name == output_filename and item.parent == target_root:
            return True

        # Use merged pattern set (base + any user-supplied extensions)
        patterns = getattr(self, "_effective_patterns", self.IGNORED_PATTERNS)

        # Exact name match  (e.g. "node_modules", "package-lock.json")
        if name in patterns:
            return True

        # Extension match  (entries in the set that start with '.')
        if any(item.name.endswith(pat) for pat in patterns if pat.startswith(".")):
            return True

        # Hidden files / dirs not explicitly whitelisted
        if name.startswith(".") and name not in {".env.example", ".editorconfig"}:
            return True

        # User-supplied absolute path exclusions
        try:
            resolved = str(item.resolve())
        except OSError:
            resolved = str(item.absolute())
        if resolved in extra_excludes:
            return True

        # .gitignore rules
        if use_gitignore and self._matches_gitignore(name, gitignore_patterns):
            return True

        return False

    def _get_children(
        self,
        dir_path: Path,
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
    ) -> list:
        """Return sorted, filtered children of dir_path (dirs first, then files)."""
        try:
            items = sorted(
                dir_path.iterdir(),
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except (PermissionError, FileNotFoundError):
            return []
        return [
            item for item in items
            if not self._should_skip(
                item, extra_excludes, gitignore_patterns,
                use_gitignore, output_filename, target_root,
            )
        ]

    # ── Statistics ────────────────────────────────────────────────────────────

    @dataclass
    class Stats:
        files: int = 0
        dirs:  int = 0
        total_bytes: int = 0

    @staticmethod
    def _format_bytes(n: int) -> str:
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024
        return f"{n:.1f} TB"

    def _collect_stats(
        self,
        dir_path: Path,
        stats: "TreeGen.Stats",
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
    ) -> None:
        """Recursively accumulate file/dir counts and total scanned bytes."""
        for item in self._get_children(
            dir_path, extra_excludes, gitignore_patterns,
            use_gitignore, output_filename, target_root,
        ):
            if item.is_dir():
                stats.dirs += 1
                self._collect_stats(
                    item, stats, extra_excludes, gitignore_patterns,
                    use_gitignore, output_filename, target_root,
                )
            else:
                stats.files += 1
                try:
                    stats.total_bytes += item.stat().st_size
                except OSError:
                    pass

    # ── Vertical renderer ─────────────────────────────────────────────────────

    def _render_vertical(
        self,
        dir_path: Path,
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
        max_depth: int,
        prefix: str = "",
        current_depth: int = 0,
    ) -> list:
        """Return lines for a classic top-down ASCII tree."""
        # Depth guard: 0 means unlimited
        if max_depth and current_depth >= max_depth:
            return []

        children = self._get_children(
            dir_path, extra_excludes, gitignore_patterns,
            use_gitignore, output_filename, target_root,
        )
        lines = []
        for i, item in enumerate(children):
            is_last   = i == len(children) - 1
            connector = "└── " if is_last else "├── "
            name      = item.name
            display   = (name[:self.MAX_NAME_LEN - 2] + "..") if len(name) > self.MAX_NAME_LEN else name

            lines.append(f"{prefix}{connector}{display}")

            if item.is_dir():
                extension = "    " if is_last else "│   "
                lines.extend(
                    self._render_vertical(
                        item, extra_excludes, gitignore_patterns,
                        use_gitignore, output_filename, target_root,
                        max_depth, prefix + extension, current_depth + 1,
                    )
                )
        return lines

    # ── Horizontal renderer ───────────────────────────────────────────────────

    def _render_horizontal(
        self,
        children: list,
        extra_excludes: set,
        gitignore_patterns: list,
        use_gitignore: bool,
        output_filename: str,
        target_root: Path,
        max_depth: int,
    ) -> list:
        """Render top-level items side-by-side, each with its own vertical subtree."""
        if not children:
            return []

        all_trees = []
        for child in children:
            sub = (
                self._render_vertical(
                    child, extra_excludes, gitignore_patterns,
                    use_gitignore, output_filename, target_root,
                    max_depth, "", 0,
                )
                if child.is_dir() else []
            )
            all_trees.append(["│"] + sub)

        col_widths = [
            max(max((len(l) for l in tree), default=0), len(child.name)) + 2
            for child, tree in zip(children, all_trees)
        ]

        spacing   = 3
        col_starts: list = []
        pos = 0
        for w in col_widths:
            col_starts.append(pos)
            pos += w + spacing
        total_width = pos - spacing

        col_centers = [col_starts[i] + col_widths[i] // 2 for i in range(len(children))]
        output_lines: list = []

        # ┌──┬──┐ top connector
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

        # │ column separators
        v_line = [" "] * total_width
        for center in col_centers:
            v_line[center] = "│"
        output_lines.append("".join(v_line))

        # Centered column names
        name_line = [" "] * total_width
        for idx, child in enumerate(children):
            name  = child.name
            start = col_centers[idx] - len(name) // 2
            for j, ch in enumerate(name):
                p = start + j
                if 0 <= p < total_width:
                    name_line[p] = ch
        output_lines.append("".join(name_line))

        # Tree rows
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


    async def execute(self, **kwargs) -> Response:
        """
        Execute tree_gen.
        Expects arguments to be available in self.args.
        """
        self._effective_patterns = self.IGNORED_PATTERNS

        input_path_str  = self.args.get("input_path", "").strip()
        output_path_str = self.args.get("output_path", input_path_str).strip()
        file_name_str   = self.args.get("file_name", "").strip()
        layout          = self.args.get("layout", "vertical").strip().lower()
        use_gitignore   = str(self.args.get("use_gitignore", "true")).lower() not in ("false", "0", "no")
        ignored_path_str= self.args.get("ignored_path", "").strip()
        ignored_ext_str = self.args.get("ignored_extensions", "").strip()
        max_depth       = int(self.args.get("max_depth", 4))

        if not input_path_str:
            return Response(message="Error: `input_path` is required.", break_loop=False)

        input_path  = Path(input_path_str).resolve()
        output_path = Path(output_path_str).resolve()

        if not input_path.exists() or not input_path.is_dir():
            return Response(
                message=f"Error: '{input_path_str}' does not exist or is not a directory.",
                break_loop=False
            )

        extra_excludes: set[str] = set()
        for p in ignored_path_str.split(","):
            p = p.strip()
            if p:
                try:
                    extra_excludes.add(str(Path(p).resolve()))
                except Exception:
                    extra_excludes.add(p)

        extra_ext_excludes: set[str] = set()
        for ext in ignored_ext_str.split(","):
            ext = ext.strip().lower()
            if ext:
                extra_ext_excludes.add(ext if ext.startswith(".") else f".{ext}")

        self._effective_patterns = self.IGNORED_PATTERNS | extra_ext_excludes

        gitignore_patterns: list[str] = []
        if use_gitignore:
            gitignore_patterns = self._load_gitignore_patterns(input_path)

        if file_name_str:
            output_filename = (
                file_name_str if file_name_str.endswith(".md") else f"{file_name_str}.md"
            )
        else:
            output_filename = f"{input_path.name}_structure.md"

        output_file_path = output_path / output_filename

        try:
            if layout == "horizontal":
                top_children = self._get_children(
                    input_path, extra_excludes, gitignore_patterns,
                    use_gitignore, output_filename, input_path,
                )
                tree_lines = self._render_horizontal(
                    top_children, extra_excludes, gitignore_patterns,
                    use_gitignore, output_filename, input_path, max_depth,
                )
            else:
                tree_lines = self._render_vertical(
                    input_path, extra_excludes, gitignore_patterns,
                    use_gitignore, output_filename, input_path, max_depth,
                )

            output_path.mkdir(parents=True, exist_ok=True)
            with open(output_file_path, "w", encoding="utf-8") as f:
                f.write(f"# Directory Structure: {input_path.name}/\n")
                f.write(f"## Path: {input_path}\n\n")
                f.write(f"{input_path.name}/\n│\n")
                for line in tree_lines:
                    f.write(line + "\n")

        except Exception as e:
            return Response(message=f"Error: {e}", break_loop=False)

        stats = self.Stats()
        self._collect_stats(
            input_path, stats, extra_excludes, gitignore_patterns,
            use_gitignore, output_filename, input_path,
        )

        line_count = len(tree_lines) + 4
        size_bytes = output_file_path.stat().st_size if output_file_path.exists() else 0
        depth_note = "unlimited" if max_depth == 0 else f"{max_depth} levels"

        response_lines = [
            "✅ Directory Structure Generated.",
            f"   Path    : {output_file_path}",
            f"   Layout  : {layout}",
            f"   Depth   : {depth_note}",
            f"   Lines   : {line_count}",
            f"   Size    : {self._format_bytes(size_bytes)}",
            f"   Dirs    : {stats.dirs}",
            f"   Files   : {stats.files}",
            f"   Scanned : {self._format_bytes(stats.total_bytes)}",
        ]

        if line_count > 500:
            response_lines.append(
                f"\n   ⚠️  Tip: Output is {line_count} lines. "
                "Consider reducing `max_depth` or adding `ignored_path` "
                "entries for a cleaner overview."
            )

        return Response(message="\n".join(response_lines), break_loop=False)
