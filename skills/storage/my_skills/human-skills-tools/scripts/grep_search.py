import os
import re
import sys
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR
for p in [_CURRENT_DIR, *_CURRENT_DIR.parents]:
    if (p / "helpers" / "tool.py").exists():
        _SKILLS_ROOT = p
        break
    if (p / "skills" / "helpers" / "tool.py").exists():
        _SKILLS_ROOT = p / "skills"
        break
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))

from helpers.tool import Tool, Response


@dataclass
class SearchResult:
    file_path: str
    line_number: Optional[int] = None
    line_content: Optional[str] = None
    node_path: Optional[str] = None
    context_type: Optional[str] = None


_SUPPORTED_EXTS: frozenset[str] = frozenset({
    "py", "js", "ts", "jsx", "tsx", "html", "css", "md",
    "java", "c", "cpp", "go", "rb", "php", "sh",
    "json", "xml", "yaml", "yml", "txt", "log", "sql",
    "r", "scala", "kt", "swift", "dart", "vue", "svelte",
})

_SKIP_DIRS: frozenset[str] = frozenset({
    "node_modules", "__pycache__", "venv", "env", ".git",
    ".mypy_cache", ".pytest_cache", "dist", "build",
})

_LANG_PATTERNS: dict[str, list[tuple[re.Pattern, str]]] = {
    "py": [
        (re.compile(r"^\s*class\s+([a-zA-Z0-9_]+)"), "class"),
        (re.compile(r"^\s*def\s+([a-zA-Z0-9_]+)"), "function"),
        (re.compile(r"^\s*async\s+def\s+([a-zA-Z0-9_]+)"), "async_function"),
    ],
    "js": [
        (re.compile(r"^\s*class\s+([a-zA-Z0-9_$]+)"), "class"),
        (re.compile(r"^\s*function\s+([a-zA-Z0-9_$]+)"), "function"),
        (re.compile(r"^\s*const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>"), "arrow_function"),
    ],
}


class GrepSearch(Tool):
    name = "grep_search"
    description = "Search for a text pattern across files in a directory, with per-line or file-level results."
    arguments = {
        "query": "Text pattern to search for. (REQUIRED)",
        "search_path": "File or directory to search in. Default: '.'.",
        "case_insensitive": "If 'true', ignore case. Default: false.",
        "match_per_line": "If 'true', return each matching line. If 'false', return filenames only. Default: true.",
        "includes": "Comma-separated glob patterns to restrict file types (e.g. '*.py,*.md').",
    }
    instruction = "For skill instructions run: human-skills --skill_info human-skills-tools"

    def _get_files(self, path: str, includes: list[str]) -> list[str]:
        base_patterns = [f"*.{ext}" for ext in _SUPPORTED_EXTS]
        active_patterns = includes if includes else base_patterns

        if os.path.isfile(path):
            return [path] if any(fnmatch.fnmatch(path, p) for p in active_patterns) else []

        files: list[str] = []
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]
            for filename in filenames:
                if filename.startswith("."):
                    continue
                fp = os.path.join(root, filename)
                if any(fnmatch.fnmatch(fp, p) or fnmatch.fnmatch(filename, p) for p in active_patterns):
                    files.append(fp)
        return files

    @staticmethod
    def _read_file(filepath: str) -> Optional[str]:
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    content = f.read()
                if len(content) <= 1_000_000:
                    return content
            except (UnicodeDecodeError, OSError):
                continue
        return None

    @staticmethod
    def _code_context(lines: list[str], line_idx: int, ext: str) -> tuple[Optional[str], Optional[str]]:
        if ext not in _LANG_PATTERNS:
            return os.path.basename(lines[0]) if lines else None, "file"
        patterns = _LANG_PATTERNS[ext]
        current_indent = len(lines[line_idx]) - len(lines[line_idx].lstrip()) if line_idx < len(lines) else 0
        context_stack: list[tuple[str, str, int]] = []
        for i in range(line_idx - 1, -1, -1):
            line = lines[i]
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            for pat, ctx_type in patterns:
                m = pat.search(line)
                if m and indent <= current_indent:
                    context_stack = [(m.group(1), ctx_type, indent)] + [c for c in context_stack if c[2] < indent]
                    current_indent = indent
                    break
            if indent == 0 and context_stack:
                break
        if not context_stack:
            return None, "module"
        if len(context_stack) > 1:
            cls_ctx = next((c for c in context_stack if c[1] == "class"), None)
            fn_ctx  = next((c for c in context_stack if c[1] in ("function", "async_function", "arrow_function")), None)
            if cls_ctx and fn_ctx:
                return f"{cls_ctx[0]}.{fn_ctx[0]}", "method"
        return context_stack[0][0], context_stack[0][1]

    def _search(
        self,
        path: str,
        query: str,
        case_insensitive: bool,
        match_per_line: bool,
        includes: list[str],
    ) -> list[SearchResult]:
        flags   = re.IGNORECASE if case_insensitive else 0
        pattern = re.compile(re.escape(query), flags)
        results: list[SearchResult] = []

        for filepath in self._get_files(path, includes):
            content = self._read_file(filepath)
            if not content:
                continue
            if match_per_line:
                lines = content.splitlines()
                ext   = os.path.splitext(filepath)[1].lstrip(".").lower()
                for i, line in enumerate(lines):
                    if pattern.search(line):
                        node, ctx = self._code_context(lines, i, ext)
                        results.append(SearchResult(
                            file_path=filepath,
                            line_number=i + 1,
                            line_content=line.strip(),
                            node_path=node,
                            context_type=ctx,
                        ))
                        if len(results) >= 100:
                            return results
            else:
                if pattern.search(content):
                    results.append(SearchResult(file_path=filepath))
                    if len(results) >= 50:
                        return results
        return results

    @staticmethod
    def _format(results: list[SearchResult], query: str, path: str, match_per_line: bool) -> str:
        if not results:
            return f"No matches found for '{query}' in {path}"

        parts = [f"Found {len(results)} match(es) for '{query}' in {path}"]

        if match_per_line:
            by_file: dict[str, list[SearchResult]] = {}
            for r in results:
                by_file.setdefault(r.file_path, []).append(r)
            for filepath, file_results in list(by_file.items())[:10]:
                rel = os.path.relpath(filepath, path) if path != "." else filepath
                parts.append(f"\n📄 {rel}")
                for r in file_results[:5]:
                    ctx = f" [{r.context_type}: {r.node_path}]" if r.node_path and r.context_type != "module" else ""
                    parts.append(f"  L{r.line_number}{ctx}: {r.line_content}")
                if len(file_results) > 5:
                    parts.append(f"  … [{len(file_results) - 5} more matches in this file]")
        else:
            for r in results[:20]:
                rel = os.path.relpath(r.file_path, path) if path != "." else r.file_path
                parts.append(f"  {rel}")

        return "\n".join(parts)

    async def execute(self, **kwargs) -> Response:
        query            = self.args.get("query", "").strip()
        path             = self.args.get("search_path", ".").strip() or "."
        case_insensitive = str(self.args.get("case_insensitive", "false")).lower() in ("true", "1", "yes")
        match_per_line   = str(self.args.get("match_per_line", "true")).lower() not in ("false", "0", "no")
        includes_raw     = self.args.get("includes", "").strip()
        includes         = [p.strip() for p in includes_raw.split(",") if p.strip()]

        if not query:
            return Response(
                message="❌ Error: 'query' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"grep_search\", \"tool_args\": {\"query\": \"def execute\", \"search_path\": \"/path/to/dir\"}}'",
                break_loop=False,
            )

        if not os.path.exists(path):
            return Response(message=f"❌ Error: Path '{path}' does not exist.", break_loop=False)

        try:
            results = self._search(path, query, case_insensitive, match_per_line, includes)
            return Response(
                message=self._format(results, query, path, match_per_line),
                break_loop=False,
                additional={"count": len(results)},
            )
        except Exception as e:
            return Response(message=f"❌ Error during search: {e}", break_loop=False)