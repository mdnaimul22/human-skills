import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import time
from typing import Optional, Union, TypedDict

from helpers.tool import Tool, Response
from helpers.files import (
    exists,
    is_file,
    is_dir,
    write_text,
    read_text,
    ensure_dir,
    delete,
    list_files,
    get_size,
    get_mtime,
    get_abs_path,
)

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

class QualityPreset(TypedDict):
    flag: str
    resolution: str
    fps: int

QUALITY_PRESETS: dict[str, dict[str, QualityPreset]] = {
    "16:9": {
        "preview": {"flag": "-ql", "resolution": "854x480", "fps": 15},
        "low": {"flag": "-ql", "resolution": "854x480", "fps": 15},
        "medium": {"flag": "-qm", "resolution": "1280x720", "fps": 30},
        "high": {"flag": "-qh", "resolution": "1920x1080", "fps": 60},
        "4k": {"flag": "-qk", "resolution": "3840x2160", "fps": 60},
    },
    "9:16": {
        "preview": {"flag": "-ql -r 480,854", "resolution": "480x854", "fps": 15},
        "low": {"flag": "-ql -r 480,854", "resolution": "480x854", "fps": 15},
        "medium": {"flag": "-qm -r 720,1280", "resolution": "720x1280", "fps": 30},
        "high": {"flag": "-qh -r 1080,1920", "resolution": "1080x1920", "fps": 60},
        "4k": {"flag": "-qk -r 2160,3840", "resolution": "2160x3840", "fps": 60},
    },
}

THEME_PALETTES: dict[str, str] = {
    "dark_slate": "#14161d",
    "midnight": "#0a0e17",
    "chalkboard": "#1b2820",
    "paper": "#f8f9fa",
    "black": "#000000",
}

class MediaProbe(TypedDict, total=False):
    file_size_bytes: int
    duration_seconds: float
    file_size_mb: float
    video_width: int
    video_height: int
    video_codec: str
    probe_error: str

class FFprobeStream(TypedDict, total=False):
    codec_type: str
    width: int
    height: int
    codec_name: str

class FFprobeFormat(TypedDict, total=False):
    duration: str

class FFprobeData(TypedDict, total=False):
    format: FFprobeFormat
    streams: list[FFprobeStream]

def _is_blocked_dunder(attr: str) -> bool:
    return (
        attr.startswith("__")
        and attr.endswith("__")
        and attr not in _ALLOWED_DUNDER_ATTRS
    )

def _scan_import_node(node: ast.Import) -> list[str]:
    violations: list[str] = []
    for alias in node.names:
        root = alias.name.split(".")[0]
        if root in _BLOCKED_IMPORTS:
            violations.append(f"import '{alias.name}'")
    return violations

def _scan_import_from_node(node: ast.ImportFrom) -> list[str]:
    root = (node.module or "").split(".")[0]
    if root in _BLOCKED_IMPORTS:
        return [f"from '{node.module}' import ..."]
    return []

def _scan_node(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return _scan_import_node(node)
    if isinstance(node, ast.ImportFrom):
        return _scan_import_from_node(node)
    if isinstance(node, ast.Name) and node.id in _BLOCKED_NAMES:
        return [f"use of '{node.id}'"]
    if isinstance(node, ast.Attribute) and _is_blocked_dunder(node.attr):
        return [f"dunder attribute access '.{node.attr}'"]
    return []

def _scan_scene_code(tree: ast.AST) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        violations.extend(_scan_node(node))

    seen: set[str] = set()
    deduped: list[str] = []
    for v in violations:
        if v not in seen:
            seen.add(v)
            deduped.append(v)
    return deduped

def _extract_modules_from_node(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.module:
        return [node.module.split(".")[0]]
    return []

def _is_latex_node(node: ast.AST) -> bool:
    if isinstance(node, ast.Name) and node.id in ("MathTex", "Tex", "Title"):
        return True
    if isinstance(node, ast.Attribute) and node.attr == "add_coordinates":
        return True
    return False

def _scan_ast_requirements(tree: ast.AST) -> tuple[list[str], bool]:
    modules: list[str] = ["manim"]
    needs_latex: bool = False
    for node in ast.walk(tree):
        modules.extend(_extract_modules_from_node(node))
        if _is_latex_node(node):
            needs_latex = True

    deduped: list[str] = []
    seen: set[str] = set()
    for m in modules:
        if m not in seen and m not in _BLOCKED_IMPORTS:
            seen.add(m)
            deduped.append(m)
    return deduped, needs_latex

def _detect_scene_name(code: str) -> Optional[str]:
    pattern = r"class\s+(\w+)\s*\(\s*(?:Scene|ThreeDScene|MovingCameraScene|ZoomedScene)\s*\)"
    matches = re.findall(pattern, code)
    if matches:
        return matches[-1]
    return None

def _find_manim_binary() -> Optional[str]:
    direct = shutil.which("manim")
    if direct:
        return direct
    candidate_paths = [
        os.path.expanduser("~/.local/bin/manim"),
        os.path.expanduser("~/.local/share/uv/tools/manim/bin/manim"),
        "/usr/local/bin/manim",
        "/usr/bin/manim",
    ]
    for path in candidate_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None

def _is_module_available(mod_name: str) -> bool:
    if mod_name == "manim":
        return _find_manim_binary() is not None
    if mod_name == "templates":
        return True
    try:
        return importlib.util.find_spec(mod_name) is not None
    except (ModuleNotFoundError, ValueError):
        return False

def _missing_system_binaries(needs_latex: bool) -> list[str]:
    missing: list[str] = []
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg")
    if needs_latex:
        if not shutil.which("latex") or not shutil.which("dvisvgm"):
            missing.append("latex")
    return missing

def _build_install_commands(missing_modules: list[str], missing_binaries: list[str]) -> list[str]:
    commands: list[str] = []
    if "manim" in missing_modules:
        uv_bin = shutil.which("uv") or os.path.expanduser("~/.local/bin/uv")
        if os.path.isfile(uv_bin) and os.access(uv_bin, os.X_OK):
            commands.append(f"{uv_bin} tool install manim")
        else:
            commands.append(f"{sys.executable} -m pip install manim")

    other_modules = [m for m in missing_modules if m != "manim"]
    if other_modules:
        mods_str = " ".join(other_modules)
        commands.append(f"{sys.executable} -m pip install {mods_str}")

    sudo_ok = subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0
    if sudo_ok and "ffmpeg" in missing_binaries:
        commands.append("sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg")
    if sudo_ok and "latex" in missing_binaries:
        commands.append("sudo apt-get update -qq && sudo apt-get install -y -qq --no-install-recommends texlive-latex-base texlive-latex-extra dvisvgm")

    return commands

def _launch_background_installer(missing_modules: list[str], missing_binaries: list[str]) -> None:
    scratch_dir = "data/scratch/math_animate"
    ensure_dir(scratch_dir)
    lock_file = f"{scratch_dir}/installer.lock"
    log_file = f"{scratch_dir}/installer.log"

    if exists(lock_file):
        age = time.time() - get_mtime(lock_file)
        if age < 600:
            return
        delete(lock_file)

    commands = _build_install_commands(missing_modules, missing_binaries)
    if not commands:
        return

    abs_lock = get_abs_path(lock_file)
    abs_log = get_abs_path(log_file)
    chained = f"touch {abs_lock} && ( " + " && ".join(commands) + f" ) > {abs_log} 2>&1 ; rm -f {abs_lock}"
    subprocess.Popen(
        ["bash", "-c", chained],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

def _ensure_libraries_installed(tree: ast.AST) -> bool:
    required_modules, needs_latex = _scan_ast_requirements(tree)
    missing_modules = [m for m in required_modules if not _is_module_available(m)]
    missing_binaries = _missing_system_binaries(needs_latex)
    if missing_modules or missing_binaries:
        _launch_background_installer(missing_modules, missing_binaries)
        return False
    return True

def _extract_stream_metadata(probe_dict: FFprobeData, info: MediaProbe) -> None:
    fmt = probe_dict.get("format")
    if fmt:
        info["duration_seconds"] = float(fmt.get("duration", 0))
    for stream in probe_dict.get("streams", []):
        if stream.get("codec_type") == "video":
            info["video_width"] = int(stream.get("width", 0))
            info["video_height"] = int(stream.get("height", 0))
            info["video_codec"] = str(stream.get("codec_name", ""))
            break

def _probe_output(path_str: str) -> MediaProbe:
    info: MediaProbe = {}
    if not exists(path_str):
        return info
    info["file_size_bytes"] = get_size(path_str)
    info["file_size_mb"] = round(info["file_size_bytes"] / (1024 * 1024), 2)
    if not shutil.which("ffprobe"):
        return info

    abs_path = get_abs_path(path_str)
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", abs_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            parsed: FFprobeData = json.loads(proc.stdout)
            _extract_stream_metadata(parsed, info)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as exc:
        info["probe_error"] = str(exc)
    return info

def _locate_rendered_file(scratch_rel: str, scene_name: str, fmt: str) -> Optional[str]:
    media_dir = f"{scratch_rel}/media"
    if not is_dir(media_dir):
        return None
    matches = list_files(media_dir, f"**/{scene_name}.{fmt}")
    if matches:
        return str(matches[0])
    fallback_matches = list_files(media_dir, f"**/*.{fmt}")
    if fallback_matches:
        return str(fallback_matches[0])
    return None

def _build_command(
    manim_bin: str,
    preset: QualityPreset,
    output_format: str,
    transparent: bool,
    scene_abs_path: str,
    scene_name: str,
) -> list[str]:
    cmd = [manim_bin] + preset["flag"].split()
    if output_format == "gif":
        cmd.extend(["--format", "gif"])
    elif output_format == "webm":
        cmd.extend(["--format", "webm"])
    elif output_format == "png":
        cmd.append("-s")
    if transparent:
        cmd.append("--transparent")
    cmd.extend(["--disable_caching", scene_abs_path, scene_name])
    return cmd

def _commit_rendered_output(
    scratch_rel: str,
    scene_name: str,
    output_format: str,
    output_target: str,
    lease_id: str,
) -> tuple[bool, Optional[str], MediaProbe]:
    rendered = _locate_rendered_file(scratch_rel, scene_name, output_format)
    if not rendered:
        return False, "Render completed but output file was not found in scratch directory.", {}

    target_parent = output_target.rsplit("/", 1)[0] if "/" in output_target else ""
    if target_parent:
        ensure_dir(target_parent)

    shadow_path = f"{output_target}.tmp_{lease_id[:8]}"
    shutil.copy2(get_abs_path(rendered), get_abs_path(shadow_path))
    video_info = _probe_output(shadow_path)
    if video_info.get("file_size_bytes", 0) == 0:
        delete(shadow_path)
        return False, "Rendered shadow file is zero bytes (integrity failure).", {}

    os.replace(get_abs_path(shadow_path), get_abs_path(output_target))
    return True, None, video_info

def _prepare_scene_script(scratch_rel: str, scene_code: str, bg_color: str) -> str:
    ensure_dir(scratch_rel)
    scene_file_rel = f"{scratch_rel}/scene.py"
    skill_abs_dir = get_abs_path("skills/storage/my_skills/math-animate")
    bg_stmt = f"config.background_color = '{bg_color}'\n" if bg_color else ""
    header = f"import sys\nsys.path.insert(0, '{skill_abs_dir}')\nfrom manim import *\nfrom templates import *\n{bg_stmt}"
    if "from manim import" in scene_code:
        injected_code = f"import sys\nsys.path.insert(0, '{skill_abs_dir}')\nfrom manim import *\nfrom templates import *\n{bg_stmt}{scene_code}"
    else:
        injected_code = f"{header}\n{scene_code}"
    write_text(scene_file_rel, injected_code)
    return scene_file_rel

def _execute_render_subprocess(cmd: list[str], scratch_rel: str) -> tuple[bool, Optional[str]]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=get_abs_path(scratch_rel))
    except subprocess.TimeoutExpired:
        return False, "Manim render timed out after 300 seconds."
    if proc.returncode != 0:
        err_msg = proc.stderr or proc.stdout or "Unknown render error"
        return False, f"Manim render failed: {err_msg.strip()[-800:]}"
    return True, None

def _format_render_report(
    target: str,
    abs_target: str,
    name: str,
    quality: str,
    aspect_ratio: str,
    preset: QualityPreset,
    output_format: str,
    bg_color: str,
    video_info: MediaProbe,
    elapsed: float,
) -> str:
    active_bg = bg_color if bg_color else "#000000 (default black)"
    lines = [
        "Mathematical Animation Rendered Successfully.",
        f"   Output (Relative) : {target}",
        f"   Output (Absolute) : {abs_target}",
        f"   Scene             : {name}",
        f"   Aspect Ratio      : {aspect_ratio}",
        f"   Quality           : {quality} ({preset['resolution']} @ {preset['fps']}fps)",
        f"   Format            : {output_format}",
        f"   Background        : {active_bg}",
        f"   Size              : {video_info.get('file_size_mb', 0)} MB",
        f"   Render Time       : {elapsed}s",
    ]
    if "duration_seconds" in video_info:
        lines.append(f"   Duration          : {video_info['duration_seconds']}s")
    if "video_width" in video_info and "video_height" in video_info:
        lines.append(f"   Dimensions        : {video_info['video_width']}x{video_info['video_height']}")
    return "\n".join(lines)

def _register_example_item(obj: dict, registry: dict, default_name: str = "") -> None:
    args = obj.get("tool_args", obj)
    name = str(args.get("scene_name", "")).strip() or default_name or str(obj.get("scene_name", "")).strip()
    if not name and "scene_code" in args:
        m = re.search(r"class\s+([A-Za-z0-9_]+)\s*\(.*Scene.*\):", str(args.get("scene_code", "")))
        if m:
            name = m.group(1)
    if name:
        registry[name] = {
            "scene_name": name,
            "quality": str(args.get("quality", "medium")),
            "format": str(args.get("format", "mp4")),
            "aspect_ratio": str(args.get("aspect_ratio", "16:9")),
            "background_color": str(args.get("background_color", "#000000")),
            "output_path": str(args.get("output_path", "")),
            "scene_code": str(args.get("scene_code", "")),
            "full_tool_args": args,
            "raw_payload": obj,
        }

def _extract_examples_from_text(raw_text: str) -> dict[str, dict]:
    examples: dict[str, dict] = {}
    cleaned = raw_text.strip()
    if cleaned.startswith("human-skills"):
        cleaned = cleaned[len("human-skills"):].strip()
    if cleaned.startswith("'") and cleaned.endswith("'"):
        cleaned = cleaned[1:-1].strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    _register_example_item(item, examples)
            return examples
        elif isinstance(data, dict):
            if "tool_args" in data or "scene_code" in data:
                _register_example_item(data, examples)
                return examples
            for k, v in data.items():
                if isinstance(v, dict):
                    _register_example_item(v, examples, default_name=k)
            if examples:
                return examples
    except Exception:
        pass

    decoder = json.JSONDecoder()
    pos = 0
    while pos < len(raw_text):
        m = re.search(r"\{", raw_text[pos:])
        if not m:
            break
        start_idx = pos + m.start()
        try:
            obj, end_idx = decoder.raw_decode(raw_text[start_idx:])
            if isinstance(obj, dict):
                _register_example_item(obj, examples)
            pos = start_idx + end_idx
        except Exception:
            pos = start_idx + 1
    return examples

def _load_all_curated_examples() -> dict[str, dict]:
    examples: dict[str, dict] = {}
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_root = os.path.dirname(script_dir)
    target_files = [
        f"{skill_root}/command.json",
        f"{skill_root}/commands.json",
        f"{skill_root}/examples.json",
        f"{skill_root}/command.txt",
    ]
    for p in target_files:
        if exists(p):
            try:
                content = read_text(p)
                extracted = _extract_examples_from_text(content)
                examples.update(extracted)
            except Exception:
                pass
    return examples

def _handle_example_request(query: str) -> Response:
    examples = _load_all_curated_examples()
    if not examples:
        return Response(
            message="No curated examples found in command.json. Add your commands to command.json to establish quality standards.",
            break_loop=False,
            additional={"examples": []},
        )
    clean_q = query.strip().lower()
    if clean_q in ("list", "all", "ls"):
        lines = [
            f"Curated Quality Standards & Examples ({len(examples)} total):",
            "--------------------------------------------------------------------------------",
        ]
        for name, item in sorted(examples.items()):
            qual = item.get("quality", "medium")
            fmt = item.get("format", "mp4")
            bg = item.get("background_color", "#000000")
            out = item.get("output_path", "")
            lines.append(f"  • scene_name: \"{name}\"  [quality: {qual} | format: {fmt} | bg: {bg}]")
            if out:
                lines.append(f"    output: {out}")
        lines.append("--------------------------------------------------------------------------------")
        lines.append("Usage to view complete code & command of an example:")
        lines.append('  human-skills \'{"tool_name": "math_animate", "tool_args": {"example": "<scene_name>"}}\'')
        return Response(
            message="\n".join(lines),
            break_loop=False,
            additional={"examples": list(examples.keys())},
        )

    matched = None
    for name, item in examples.items():
        if name.lower() == clean_q:
            matched = item
            break

    if not matched:
        return Response(
            message=f"Example '{query}' not found in db.\nAvailable scene_names:\n  • " + "\n  • ".join(sorted(examples.keys())),
            break_loop=False,
            success=False,
        )

    s_name = matched.get("scene_name", "")
    s_code = matched.get("scene_code", "")
    qual = matched.get("quality", "medium")
    fmt = matched.get("format", "mp4")
    ar = matched.get("aspect_ratio", "16:9")
    bg = matched.get("background_color", "#000000")
    out = matched.get("output_path", "")

    full_cmd = json.dumps({
        "tool_name": "math_animate",
        "tool_args": matched.get("full_tool_args", {})
    }, indent=2, ensure_ascii=False)

    lines = [
        "================================================================================",
        f"Curated Example: {s_name}",
        "================================================================================",
        f"Scene Name       : {s_name}",
        f"Quality          : {qual}",
        f"Aspect Ratio     : {ar}",
        f"Format           : {fmt}",
        f"Background Color : {bg}",
        f"Output Path      : {out}",
        "",
        "Scene Code:",
        "--------------------------------------------------------------------------------",
        s_code,
        "--------------------------------------------------------------------------------",
        "",
        "Execution Command:",
        f"human-skills '{full_cmd}'",
        "================================================================================",
    ]
    return Response(
        message="\n".join(lines),
        break_loop=False,
        additional={
            "example_found": True,
            "scene_name": s_name,
            "scene_code": s_code,
            "tool_args": matched.get("full_tool_args", {}),
        },
    )

class MathAnimate(Tool):
    name = "math_animate"
    description = "Render mathematical, geometric, and scientific animations into MP4, GIF, WebM, or PNG using Manim Community Edition."
    arguments = {
        "example": "View curated list of examples from db. Pass 'list' to see all scene_names, or pass '<scene_name>' to view its full code and command. Optional.",
        "scene_code": "Python code defining a Manim Scene with a construct() method. (REQUIRED when not using example)",
        "scene_name": "Name of the Scene class to render. Default: auto-detected.",
        "output_path": "Path to save the rendered output (e.g. 'data/scene.mp4'). If path does not start with data/, it will automatically be placed under data/. Default: 'data/math_animate/<SceneName>_<timestamp>.<format>'.",
        "aspect_ratio": "Video aspect ratio: '16:9' (standard landscape) or '9:16' (mobile-friendly vertical for Shorts/Reels/TikTok). Default: '16:9'.",
        "quality": "Quality preset: 'preview' (fast draft), 'low' (480p), 'medium' (720p), 'high' (1080p), '4k' (2160p). Default: 'medium'.",
        "format": "Output format: 'mp4', 'gif', 'png', 'webm'. Default: 'mp4' (or 'gif' when quality is preview and format is omitted).",
        "transparent": "If 'true', render with transparent background. Default: false.",
        "background_color": "Hex background color (e.g. '#1a1a2e'). Default: black.",
        "allow_unsafe_code": "If 'true', bypass the AST security denylist scan. Default: false.",
    }
    instruction = "For skill instructions run: human-skills --skill_info math-animate"

    async def execute(self, **kwargs) -> Response:
        example_req = str(self.args.get("example", "")).strip()
        if example_req:
            return _handle_example_request(example_req)

        scene_code = str(self.args.get("scene_code", "")).strip()
        if not scene_code:
            return Response(message="Error: 'scene_code' is required.", break_loop=False)

        try:
            tree = ast.parse(scene_code)
        except SyntaxError as e:
            return Response(message=f"Pre-Commit Syntax Error in scene_code: {e}", break_loop=False)

        allow_unsafe = str(self.args.get("allow_unsafe_code", "false")).lower() in ("true", "1", "yes")
        if not allow_unsafe:
            violations = _scan_scene_code(tree)
            if violations:
                return Response(
                    message="Security Error: scene_code blocked by safety scan: " + ", ".join(violations),
                    break_loop=False,
                )

        if not _ensure_libraries_installed(tree):
            return Response(
                message="required lib not found , we are installing, please wite sometimes then execute tool again.",
                break_loop=False,
            )

        scene_name = str(self.args.get("scene_name", "")).strip() or _detect_scene_name(scene_code)
        if not scene_name:
            return Response(message="Error: Could not detect Scene class name from scene_code.", break_loop=False)

        raw_aspect = str(self.args.get("aspect_ratio", "16:9")).strip().lower()
        aspect_ratio = "9:16" if raw_aspect in ("9:16", "vertical", "portrait") else "16:9"

        raw_quality = str(self.args.get("quality", "medium")).strip().lower()
        quality = raw_quality if raw_quality in QUALITY_PRESETS[aspect_ratio] else "medium"

        raw_format = str(self.args.get("format", "")).strip().lower()
        if not raw_format:
            output_format = "gif" if quality == "preview" else "mp4"
        else:
            output_format = raw_format if raw_format in ("mp4", "gif", "png", "webm") else "mp4"

        transparent = str(self.args.get("transparent", "false")).lower() in ("true", "1", "yes")
        raw_bg = str(self.args.get("background_color", "")).strip()
        bg_color = THEME_PALETTES.get(raw_bg.lower(), raw_bg)

        raw_output_path = str(self.args.get("output_path", "")).strip()
        timestamp = int(time.time())
        if raw_output_path:
            clean_path = raw_output_path.lstrip("/")
            if not clean_path.startswith("data/"):
                output_target = f"data/{clean_path}"
            else:
                output_target = clean_path
        else:
            output_target = f"data/math_animate/{scene_name}_{timestamp}.{output_format}"

        lease_id = hashlib.sha256(f"{scene_code}:{timestamp}:{time.time()}".encode("utf-8")).hexdigest()[:12]
        scratch_rel = f"data/scratch/math_animate/lease_{lease_id}"
        scene_file_rel = _prepare_scene_script(scratch_rel, scene_code, bg_color)
        preset = QUALITY_PRESETS[aspect_ratio][quality]
        manim_bin = _find_manim_binary() or "manim"
        cmd = _build_command(
            manim_bin,
            preset,
            output_format,
            transparent,
            get_abs_path(scene_file_rel),
            scene_name,
        )

        start_time = time.time()
        success, exec_err = _execute_render_subprocess(cmd, scratch_rel)
        if not success:
            delete(scratch_rel)
            return Response(message=str(exec_err), break_loop=False)

        committed, commit_err, video_info = _commit_rendered_output(
            scratch_rel, scene_name, output_format, output_target, lease_id
        )
        delete(scratch_rel)

        if not committed:
            return Response(message=f"Commit Error: {commit_err}", break_loop=False)

        elapsed = round(time.time() - start_time, 2)
        abs_target = get_abs_path(output_target)
        report_msg = _format_render_report(
            output_target, abs_target, scene_name, quality, aspect_ratio, preset, output_format, bg_color, video_info, elapsed
        )
        return Response(
            message=report_msg,
            break_loop=False,
            additional={
                "output_path": output_target,
                "absolute_path": abs_target,
                "scene_name": scene_name,
                "aspect_ratio": aspect_ratio,
                "quality": quality,
                "format": output_format,
                "background_color": bg_color,
                **video_info,
            },
        )
