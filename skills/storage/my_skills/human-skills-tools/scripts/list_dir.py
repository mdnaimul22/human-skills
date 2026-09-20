import os
import sys
import stat
import datetime
from pathlib import Path

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


class ListDir(Tool):
    name = "list_dir"
    description = "List directory contents with type, size, and modification time in a markdown table."
    arguments = {
        "directory_path": "Absolute path to the directory to list. (REQUIRED)",
    }
    instruction = "For skill instructions run: human-skills --skill_info human-skills-tools"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        if size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        if size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def _format_permissions(mode: int) -> str:
        checks = [
            (stat.S_IRUSR, "r"), (stat.S_IWUSR, "w"), (stat.S_IXUSR, "x"),
            (stat.S_IRGRP, "r"), (stat.S_IWGRP, "w"), (stat.S_IXGRP, "x"),
            (stat.S_IROTH, "r"), (stat.S_IWOTH, "w"), (stat.S_IXOTH, "x"),
        ]
        return "".join(c if mode & flag else "-" for flag, c in checks)

    @staticmethod
    def _count_files(directory: str) -> int:
        count = 0
        try:
            for _, _, files in os.walk(directory):
                count += len(files)
        except OSError:
            pass
        return count

    def _build_table(self, directory_path: str, entries: list[str]) -> str:
        if not entries:
            return f"Directory '{directory_path}' is empty."

        lines = [
            f"Contents of `{directory_path}`:\n",
            "| Name | Type | Size | Modified | Permissions |",
            "|------|------|------|----------|-------------|",
        ]
        for entry in entries:
            full = os.path.join(directory_path, entry)
            try:
                st       = os.stat(full)
                is_dir   = os.path.isdir(full)
                etype    = "Dir" if is_dir else "File"
                size_str = f"{self._count_files(full)} files" if is_dir else self._format_size(st.st_size)
                mtime    = datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
                perms    = self._format_permissions(st.st_mode)
                label    = f"{entry}/" if is_dir else entry
                lines.append(f"| {label} | {etype} | {size_str} | {mtime} | {perms} |")
            except OSError as e:
                lines.append(f"| {entry} | — | — | — | {e} |")
        return "\n".join(lines)

    async def execute(self, **kwargs) -> Response:
        directory_path = self.args.get("directory_path", "").strip()

        if not directory_path:
            return Response(
                message="❌ Error: 'directory_path' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"list_dir\", \"tool_args\": {\"directory_path\": \"/path/to/dir\"}}'",
                break_loop=False,
            )

        if not os.path.isdir(directory_path):
            return Response(
                message=f"❌ Error: '{directory_path}' is not a valid directory.",
                break_loop=False,
            )

        try:
            entries = sorted(
                os.listdir(directory_path),
                key=lambda x: (0 if os.path.isdir(os.path.join(directory_path, x)) else 1, x.lower()),
            )
            return Response(
                message=self._build_table(directory_path, entries),
                break_loop=False,
                additional={"count": len(entries), "path": directory_path},
            )
        except Exception as e:
            return Response(message=f"❌ Error listing directory: {e}", break_loop=False)
