import ast
import json
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Optional

from helpers.tool import Tool, Response
from helpers.files import exists, is_file, ensure_dir

_BLOCKED_IMPORTS = frozenset({
    "os", "sys", "subprocess", "socket", "shutil", "requests", "urllib",
    "http", "ftplib", "smtplib", "telnetlib", "ctypes", "pickle", "marshal",
    "importlib", "builtins", "multiprocessing", "threading", "pty", "glob",
    "resource", "signal", "tempfile", "webbrowser", "pathlib",
})

_BLOCKED_NAMES = frozenset({
    "eval", "exec", "compile", "__import__", "open", "input", "breakpoint",
    "__builtins__", "__loader__", "globals", "locals", "vars",
    "getattr", "setattr", "delattr",
})

_ALLOWED_DUNDER_ATTRS = frozenset({"__init__", "__name__"})

QUALITY_PRESETS = {
    "low": {"flag": "-ql", "resolution": "854x480", "fps": 15},
    "medium": {"flag": "-qm", "resolution": "1280x720", "fps": 30},
    "high": {"flag": "-qh", "resolution": "1920x1080", "fps": 60},
    "4k": {"flag": "-qk", "resolution": "3840x2160", "fps": 60},
    "preview": {"flag": "-ql --format gif", "resolution": "854x480", "fps": 15},
}


def _is_blocked_dunder(attr: str) -> bool:
    return (
        attr.startswith("__")
        and attr.endswith("__")
        and attr not in _ALLOWED_DUNDER_ATTRS
    )


def _scan_scene_code(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in _BLOCKED_IMPORTS:
                    violations.append(f"import '{alias.name}'")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if root in _BLOCKED_IMPORTS:
                violations.append(f"from '{node.module}' import ...")
        elif isinstance(node, ast.Name):
            if node.id in _BLOCKED_NAMES:
                violations.append(f"use of '{node.id}'")
        elif isinstance(node, ast.Attribute):
            if _is_blocked_dunder(node.attr):
                violations.append(f"dunder attribute access '.{node.attr}'")

    seen: set[str] = set()
    deduped: list[str] = []
    for v in violations:
        if v not in seen:
            seen.add(v)
            deduped.append(v)
    return deduped


def _detect_scene_name(code: str) -> Optional[str]:
    pattern = r"class\s+(\w+)\s*\(\s*(?:Scene|ThreeDScene|MovingCameraScene|ZoomedScene)\s*\)"
    matches = re.findall(pattern, code)
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        return matches[-1]
    return None


def _find_output(work_dir: Path, scene_name: str, fmt: str) -> Optional[Path]:
    media_dir = work_dir / "media"
    if not media_dir.exists():
        return None

    ext_map = {"mp4": ".mp4", "gif": ".gif", "webm": ".webm", "png": ".png"}
    target_ext = ext_map.get(fmt, ".mp4")

    for path in media_dir.rglob(f"{scene_name}{target_ext}"):
        return path

    for path in media_dir.rglob(f"*{target_ext}"):
        return path

    return None


def _probe_output(path: Path) -> dict[str, Any]:
    info: dict[str, Any] = {"file_size_bytes": path.stat().st_size}
    if not shutil.which("ffprobe"):
        return info

    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            probe = json.loads(proc.stdout)
            fmt = probe.get("format", {})
            info["duration_seconds"] = float(fmt.get("duration", 0))
            info["file_size_mb"] = round(path.stat().st_size / (1024 * 1024), 2)
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    info["video_width"] = int(stream.get("width", 0))
                    info["video_height"] = int(stream.get("height", 0))
                    info["video_codec"] = stream.get("codec_name", "")
                    break
    except Exception:
        pass
    return info


class MathAnimate(Tool):
    name = "math_animate"
    description = "Render mathematical, geometric, and scientific animations into MP4, GIF, WebM, or PNG using Manim Community Edition."
    arguments = {
        "scene_code": "Python code defining a Manim Scene with a construct() method. (REQUIRED)",
        "scene_name": "Name of the Scene class to render. Default: auto-detected.",
        "output_path": "Path to save the rendered output (e.g. 'output/scene.mp4'). Default: 'manim_<SceneName>.<format>'.",
        "quality": "Quality preset: 'low' (480p), 'medium' (720p), 'high' (1080p), '4k' (2160p), 'preview' (GIF). Default: 'medium'.",
        "format": "Output format: 'mp4', 'gif', 'png', 'webm'. Default: 'mp4'.",
        "transparent": "If 'true', render with transparent background. Default: false.",
        "background_color": "Hex background color (e.g. '#1a1a2e'). Default: black.",
        "allow_unsafe_code": "If 'true', bypass the AST security denylist scan. Default: false.",
    }
    instruction = "For skill instructions run: human-skills --skill_info math-animate"

    async def execute(self, **kwargs) -> Response:
        scene_code = self.args.get("scene_code", "").strip()
        if not scene_code:
            return Response(
                message="❌ Error: 'scene_code' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"math_animate\", \"tool_args\": {\"scene_code\": \"class MyScene(Scene):\\n    def construct(self):\\n        self.play(Create(Circle()))\"}}'",
                break_loop=False,
            )

        if not shutil.which("manim"):
            return Response(
                message="❌ Error: 'manim' CLI is not found in PATH.\n"
                        "Install Manim Community Edition:\n"
                        "  pip install manim\n"
                        "Requires: Python 3.8+, FFmpeg (installed), LaTeX (optional, for math equations).",
                break_loop=False,
            )

        allow_unsafe = str(self.args.get("allow_unsafe_code", "false")).lower() in ("true", "1", "yes")
        if not allow_unsafe:
            violations = _scan_scene_code(scene_code)
            if violations:
                return Response(
                    message="❌ Security Error: scene_code blocked by safety scan.\n"
                            "The following disallowed constructs were detected:\n  - "
                            + "\n  - ".join(violations)
                            + "\n\nIf you trust this code and need these constructs, pass \"allow_unsafe_code\": \"true\".",
                    break_loop=False,
                )

        scene_name = self.args.get("scene_name", "").strip()
        if not scene_name:
            scene_name = _detect_scene_name(scene_code)
            if not scene_name:
                return Response(
                    message="❌ Error: Could not detect Scene class name from scene_code.\n"
                            "Provide 'scene_name' explicitly (e.g. \"scene_name\": \"MyScene\").",
                    break_loop=False,
                )

        quality = self.args.get("quality", "medium").strip().lower()
        if quality not in QUALITY_PRESETS:
            quality = "medium"

        output_format = self.args.get("format", "mp4").strip().lower()
        if output_format not in ("mp4", "gif", "png", "webm"):
            output_format = "mp4"

        output_path_str = self.args.get("output_path", "").strip()
        transparent = str(self.args.get("transparent", "false")).lower() in ("true", "1", "yes")
        bg_color = self.args.get("background_color", "").strip()

        if "from manim import" not in scene_code:
            scene_code = "from manim import *\n\n" + scene_code

        work_dir = Path(tempfile.mkdtemp(prefix="manim_"))
        scene_file = work_dir / "scene.py"
        scene_file.write_text(scene_code, encoding="utf-8")

        preset = QUALITY_PRESETS[quality]
        cmd = ["manim"]
        for flag_part in preset["flag"].split():
            cmd.append(flag_part)

        if output_format == "gif":
            cmd.extend(["--format", "gif"])
        elif output_format == "webm":
            cmd.extend(["--format", "webm"])
        elif output_format == "png":
            cmd.append("-s")

        if transparent:
            cmd.append("--transparent")

        if bg_color:
            cmd.extend(["--background_color", bg_color])

        cmd.append("--disable_caching")
        cmd.append(str(scene_file))
        cmd.append(scene_name)

        start_time = time.time()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(work_dir),
            )
        except subprocess.TimeoutExpired:
            shutil.rmtree(str(work_dir), ignore_errors=True)
            return Response(message="❌ Error: Manim render timed out after 300 seconds.", break_loop=False)

        if proc.returncode != 0:
            error_msg = proc.stderr or proc.stdout or "Unknown render error"
            lines = error_msg.strip().split("\n")
            error_lines = [l for l in lines if any(k in l for k in ("Error", "error", "Traceback"))]
            if error_lines:
                error_msg = "\n".join(lines[lines.index(error_lines[0]):])
            shutil.rmtree(str(work_dir), ignore_errors=True)
            return Response(message=f"❌ Manim render failed:\n{error_msg}", break_loop=False)

        rendered_file = _find_output(work_dir, scene_name, output_format)
        if not rendered_file:
            shutil.rmtree(str(work_dir), ignore_errors=True)
            return Response(
                message=f"❌ Render succeeded but output file was not found.\n{proc.stdout}",
                break_loop=False,
            )

        if output_path_str:
            final_path = Path(output_path_str).resolve()
        else:
            final_path = Path.cwd() / f"manim_{scene_name}{rendered_file.suffix}"

        final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(rendered_file), str(final_path))
        video_info = _probe_output(final_path)
        shutil.rmtree(str(work_dir), ignore_errors=True)

        elapsed = round(time.time() - start_time, 2)
        size_bytes = video_info.get("file_size_bytes", final_path.stat().st_size)
        size_s = f"{size_bytes / (1024 * 1024):.1f} MB" if size_bytes >= 1024 * 1024 else f"{size_bytes / 1024:.1f} KB"

        report_lines = [
            "✅ Mathematical Animation Rendered Successfully.",
            f"   Output      : {final_path}",
            f"   Scene       : {scene_name}",
            f"   Quality     : {quality} ({preset['resolution']} @ {preset['fps']}fps)",
            f"   Format      : {output_format}",
            f"   Size        : {size_s}",
            f"   Render Time : {elapsed}s",
        ]
        if "duration_seconds" in video_info:
            report_lines.append(f"   Duration    : {video_info['duration_seconds']}s")

        return Response(
            message="\n".join(report_lines),
            break_loop=False,
            additional={
                "output": str(final_path),
                "scene_name": scene_name,
                "quality": quality,
                "format": output_format,
                **video_info,
            },
        )
