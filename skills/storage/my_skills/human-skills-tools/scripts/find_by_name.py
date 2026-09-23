import os
import sys
import subprocess
from pathlib import Path

from helpers.tool import Tool, Response
from helpers.files import is_dir, is_file


class FindByName(Tool):
    name = "find_by_name"
    description = "Find files or directories by name or glob pattern using the system find command."
    arguments = {
        "search_directory": "Root directory to search in. (REQUIRED)",
        "pattern": "Filename glob pattern (e.g. '*.py'). Default: '*'.",
        "type": "'file', 'directory', or 'any'. Default: 'any'.",
        "max_depth": "Maximum directory depth to search. Default: unlimited.",
        "excludes": "Comma-separated sub-path segments to exclude (e.g. 'node_modules,__pycache__').",
        "full_path": "If 'true', match pattern against full path instead of filename only. Default: false.",
    }
    instruction = "For skill instructions run: human-skills --skill_info human-skills-tools"

    @staticmethod
    def _format_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        if size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        return f"{size / (1024 * 1024 * 1024):.1f} GB"

    @staticmethod
    def _format_results(results: list[dict], search_directory: str, pattern: str) -> str:
        if not results:
            return f"No files found matching '{pattern}' in {search_directory}"

        lines = [f"Found {len(results)} result(s) matching '{pattern}' in {search_directory}:"]
        for info in results[:50]:
            rel = os.path.relpath(info["path"], search_directory)
            if info["is_dir"]:
                lines.append(f"  {rel}/ (directory)")
            else:
                lines.append(f"  {rel} ({FindByName._format_size(info['size'])})")
        if len(results) > 50:
            lines.append(f"  … [{len(results) - 50} more results not shown]")
        return "\n".join(lines)

    async def execute(self, **kwargs) -> Response:
        search_directory = self.args.get("search_directory", "").strip()
        pattern          = self.args.get("pattern", "*").strip() or "*"
        file_type        = self.args.get("type", "any").strip().lower()
        max_depth        = self.args.get("max_depth", "").strip()
        excludes_raw     = self.args.get("excludes", "").strip()
        full_path        = str(self.args.get("full_path", "false")).lower() in ("true", "1", "yes")

        if not search_directory:
            return Response(
                message="❌ Error: 'search_directory' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"find_by_name\", \"tool_args\": {\"search_directory\": \"/path/to/dir\", \"pattern\": \"*.py\"}}'",
                break_loop=False,
            )

        if not is_dir(search_directory):
            return Response(
                message=f"❌ Error: Directory '{search_directory}' does not exist.",
                break_loop=False,
            )

        cmd = ["find", search_directory]

        if max_depth:
            try:
                cmd.extend(["-maxdepth", str(int(max_depth))])
            except ValueError:
                pass

        if file_type == "file":
            cmd.extend(["-type", "f"])
        elif file_type == "directory":
            cmd.extend(["-type", "d"])

        if pattern != "*":
            cmd.extend(["-path" if full_path else "-name", pattern])

        excludes = [e.strip() for e in excludes_raw.split(",") if e.strip()]
        for exc in excludes:
            cmd.extend(["-not", "-path", f"*/{exc}/*"])

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            raw_paths = [l.strip() for l in proc.stdout.splitlines() if l.strip()]

            results: list[dict] = []
            for p in raw_paths:
                try:
                    st = os.stat(p)
                    results.append({
                        "path": p,
                        "is_dir": is_dir(p),
                        "size": st.st_size if is_file(p) else 0,
                    })
                except OSError:
                    continue

            return Response(
                message=self._format_results(results, search_directory, pattern),
                break_loop=False,
                additional={"count": len(results)},
            )

        except subprocess.TimeoutExpired:
            return Response(message="❌ Error: find command timed out after 30 seconds.", break_loop=False)
        except Exception as e:
            return Response(message=f"❌ Error executing find: {e}", break_loop=False)
