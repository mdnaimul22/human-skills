import os
import ast
import sys
import json
import tempfile
import subprocess
from dataclasses import dataclass
from pathlib import Path

from helpers.tool import Tool, Response
from helpers.files import exists, write_text


@dataclass
class _CheckResult:
    valid: bool
    errors: list[str]
    warnings: list[str]


def _check_python(content: str) -> _CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not content.strip():
        return _CheckResult(True, [], [])
    try:
        ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Python SyntaxError: {e.msg} at line {e.lineno}")
    except Exception as e:
        errors.append(f"Python parse error: {e}")
    return _CheckResult(len(errors) == 0, errors, warnings)


def _check_json(content: str) -> _CheckResult:
    errors: list[str] = []
    if not content.strip():
        return _CheckResult(True, [], [])
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON error: {e.msg} at L{e.lineno}:{e.colno}")
    return _CheckResult(len(errors) == 0, errors, [])


def _check_yaml(content: str) -> _CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    if not content.strip():
        return _CheckResult(True, [], [])
    try:
        import yaml
        yaml.safe_load(content)
    except ImportError:
        warnings.append("PyYAML not installed — YAML syntax check skipped.")
    except Exception as e:
        errors.append(f"YAML error: {e}")
    return _CheckResult(len(errors) == 0, errors, warnings)


def _check_xml(content: str) -> _CheckResult:
    errors: list[str] = []
    if not content.strip():
        return _CheckResult(True, [], [])
    try:
        import xml.etree.ElementTree as ET
        ET.fromstring(content)
    except Exception as e:
        errors.append(f"XML error: {e}")
    return _CheckResult(len(errors) == 0, errors, [])


_CHECKERS: dict[str, callable] = {
    ".py":   _check_python,
    ".json": _check_json,
    ".yaml": _check_yaml,
    ".yml":  _check_yaml,
    ".xml":  _check_xml,
}


def _validate(content: str, target_file: str) -> _CheckResult:
    ext = Path(target_file).suffix.lower()
    checker = _CHECKERS.get(ext)
    if not checker:
        return _CheckResult(True, [], [f"No syntax checker for '{ext}' files — skipped."])
    result = checker(content)
    if result.errors:
        return result
    if ext == ".py":
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False)
        try:
            tmp.write(content)
            tmp.close()
            r = subprocess.run(
                [sys.executable, "-m", "py_compile", tmp.name],
                capture_output=True, text=True, timeout=10,
            )
            if r.returncode != 0:
                result.errors.append(f"py_compile: {r.stderr.strip()}")
                result.valid = False
        except Exception:
            pass
        finally:
            os.unlink(tmp.name)
    return result


class WriteToFile(Tool):
    name = "write_to_file"
    description = "Create a new file with the provided content, with optional syntax validation."
    arguments = {
        "target_file": "Absolute path for the new file. (REQUIRED)",
        "code_content": "Content to write to the file. Default: empty string.",
        "overwrite": "If 'true', overwrite an existing file. Default: false.",
        "auto_check": "If 'true', validate syntax before writing. Default: true.",
        "strict_mode": "If 'true', block file creation on syntax errors. Default: true.",
    }
    instruction = "For skill instructions run: human-skills --skill_info human-skills-tools"

    async def execute(self, **kwargs) -> Response:
        target_file  = self.args.get("target_file", "").strip()
        code_content = self.args.get("code_content", "")
        overwrite    = str(self.args.get("overwrite", "false")).lower() in ("true", "1", "yes")
        auto_check   = str(self.args.get("auto_check", "true")).lower() not in ("false", "0", "no")
        strict_mode  = str(self.args.get("strict_mode", "true")).lower() not in ("false", "0", "no")

        if not target_file:
            return Response(
                message="❌ Error: 'target_file' is required.\n"
                        "Example: human-skills '{\"tool_name\": \"write_to_file\", \"tool_args\": {\"target_file\": \"/path/to/file.py\", \"code_content\": \"print(1)\"}}'",
                break_loop=False,
            )

        if exists(target_file) and not overwrite:
            return Response(
                message=f"❌ Error: '{target_file}' already exists. Pass \"overwrite\": \"true\" to replace it.",
                break_loop=False,
            )

        check_result: _CheckResult | None = None
        if auto_check and code_content.strip():
            check_result = _validate(code_content, target_file)
            if strict_mode and not check_result.valid:
                error_lines = ["❌ Syntax validation failed — file NOT created.", ""]
                error_lines += [f"  × {err}" for err in check_result.errors]
                if check_result.warnings:
                    error_lines += [""] + [f"  ! {w}" for w in check_result.warnings]
                error_lines.append("\n🔧 Fix the errors above and retry.")
                return Response(message="\n".join(error_lines), break_loop=False)

        try:
            write_text(target_file, code_content)
        except Exception as e:
            return Response(message=f"❌ Error writing file: {e}", break_loop=False)

        size   = len(code_content.encode("utf-8"))
        size_s = f"{size / 1024:.1f} KB" if size >= 1024 else f"{size} B"
        lines  = [
            f"✅ File created: {target_file}",
            f"   Size    : {size_s}",
            f"   Lines   : {len(code_content.splitlines())}",
        ]
        if check_result:
            lines.append("   Syntax  : ✓ passed" if check_result.valid else "   Syntax  : ⚠️  warnings (file created anyway)")
            if check_result.warnings:
                for w in check_result.warnings:
                    lines.append(f"   ! {w}")

        return Response(
            message="\n".join(lines),
            break_loop=False,
            additional={"path": target_file, "size_bytes": size},
        )