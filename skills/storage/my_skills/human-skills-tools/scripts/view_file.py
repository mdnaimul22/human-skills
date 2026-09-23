import os
import sys
import time
import hashlib
from pathlib import Path
from typing import Optional

from helpers.tool import Tool, Response
from helpers.files import is_file

_FILE_CACHE: dict[str, dict] = {}
_MAX_CACHE_ENTRIES = 50
_MAX_FILE_BYTES    = 50 * 1024 * 1024


def _evict_cache() -> None:
    if len(_FILE_CACHE) > _MAX_CACHE_ENTRIES:
        items = sorted(_FILE_CACHE.items(), key=lambda x: x[1].get("last_access", 0))
        for k, _ in items[: len(_FILE_CACHE) - _MAX_CACHE_ENTRIES + 10]:
            del _FILE_CACHE[k]


def _detect_encoding(path: str) -> str:
    try:
        import chardet
        with open(path, "rb") as f:
            raw = f.read(min(10_000, os.path.getsize(path)))
        result = chardet.detect(raw)
        return result.get("encoding") or "utf-8"
    except Exception:
        return "utf-8"


def _read_lines(path: str, start: int = 1, end: Optional[int] = None) -> tuple[list[str], int]:
    try:
        st    = os.stat(path)
        size  = st.st_size
        mtime = st.st_mtime
        key   = f"{path}:{size}:{mtime}"

        if key in _FILE_CACHE:
            entry = _FILE_CACHE[key]
            entry["last_access"] = time.time()
            all_lines = entry["lines"]
            total     = len(all_lines)
            s = max(0, start - 1)
            e = end if end is None else min(total, end)
            return all_lines[s:e], total

        if size > _MAX_FILE_BYTES:
            return _read_large(path, start, end)

        enc = _detect_encoding(path)
        with open(path, "r", encoding=enc, errors="replace") as f:
            all_lines = f.readlines()

        _FILE_CACHE[key] = {"lines": all_lines, "last_access": time.time(), "size": size}
        _evict_cache()

        total = len(all_lines)
        s = max(0, start - 1)
        e = end if end is None else min(total, end)
        return all_lines[s:e], total

    except Exception as exc:
        return [f"Error reading file: {exc}"], 0


def _read_large(path: str, start: int, end: Optional[int]) -> tuple[list[str], int]:
    enc   = _detect_encoding(path)
    lines = []
    total = 0
    try:
        with open(path, "r", encoding=enc, errors="replace") as f:
            for i, line in enumerate(f, start=1):
                total = i
                if i < start:
                    continue
                if end is not None and i > end:
                    continue
                lines.append(line)
        return lines, total
    except Exception as exc:
        return [f"Error reading large file: {exc}"], 0


class ViewFile(Tool):
    name = "view_file"
    description = "Read and display the contents of a file, with optional line range and numbered output."
    arguments = {
        "absolute_path": "Absolute path to the file to view. (REQUIRED)",
        "start_line": "First line to display (1-indexed). Default: 1.",
        "end_line": "Last line to display (inclusive). Default: show all.",
    }
    instruction = "For skill instructions run: human-skills --skill_info human-skills-tools"

    async def execute(self, **kwargs) -> Response:
        path = self.args.get("absolute_path", "").strip()

        if not path:
            return Response(
                message="❌ Error: 'absolute_path' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"view_file\", \"tool_args\": {\"absolute_path\": \"/path/to/file.py\"}}'",
                break_loop=False,
            )

        if not is_file(path):
            return Response(message=f"❌ Error: File '{path}' not found.", break_loop=False)

        try:
            start_line = int(self.args.get("start_line", 1))
        except (TypeError, ValueError):
            start_line = 1

        end_arg = self.args.get("end_line")
        try:
            end_line: Optional[int] = int(end_arg) if end_arg else None
        except (TypeError, ValueError):
            end_line = None

        try:
            lines, total = _read_lines(path, start=start_line, end=end_line)

            if total == 0 and os.path.getsize(path) == 0:
                return Response(message="(empty file)", break_loop=False)

            if not lines:
                return Response(message=f"❌ Could not read lines from '{path}'.", break_loop=False)

            offset      = start_line - 1
            numbered    = [f"{offset + i + 1}: {line.rstrip(chr(10))}" for i, line in enumerate(lines)]
            content     = "\n".join(numbered)
            MAX_CHARS   = 100_000
            truncated   = len(content) > MAX_CHARS
            if truncated:
                content = content[:MAX_CHARS] + "\n… [output truncated — use start_line/end_line to view the rest]"

            header = (
                f"File: {path}  |  Total lines: {total}"
                + (f"  |  Showing: L{start_line}–L{end_line or total}" if start_line > 1 or end_line else "")
            )

            return Response(
                message=f"{header}\n{'─' * min(len(header), 80)}\n{content}",
                break_loop=False,
                additional={"path": path, "total_lines": total, "truncated": truncated},
            )

        except Exception as e:
            return Response(message=f"❌ Unexpected error reading '{path}': {e}", break_loop=False)