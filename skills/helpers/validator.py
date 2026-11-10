import ast
import json
import os
import re
import shutil
import subprocess
import time
import tomllib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import Callable, TypedDict

try:
    from helpers.files import exists, ensure_dir, delete, get_mtime, get_abs_path
except ImportError:
    from skills.helpers.files import exists, ensure_dir, delete, get_mtime, get_abs_path


class SchemaRule(TypedDict, total=False):
    parser: str
    checks: list[str]
    severity: str
    note: str


VALIDATION_SCHEMA: dict[str, SchemaRule | str | None] = {
    ".py": {
        "parser": "ast.parse",
        "checks": ["syntax_tree_parse"],
        "severity": "strict",
    },
    ".json": {
        "parser": "json.loads",
        "checks": ["json_decode"],
        "severity": "strict",
    },
    ".yaml": {
        "parser": "yaml.safe_load",
        "checks": ["yaml_parse"],
        "severity": "strict",
        "note": "warning if PyYAML not installed",
    },
    ".yml": ".yaml",
    ".toml": {
        "parser": "tomllib.loads",
        "checks": ["toml_parse"],
        "severity": "strict",
    },
    ".xml": {
        "parser": "xml.etree.ElementTree.fromstring",
        "checks": ["xml_wellformed"],
        "severity": "strict",
    },
    ".svg": ".xml",
    ".xhtml": ".xml",
    ".html": {
        "parser": "html.parser+acorn",
        "checks": [
            "tag_matching",
            "void_element_rules",
            "unclosed_tags",
            "malformed_syntax",
            "comment_integrity",
            "script_syntax_ast",
            "script_scope_symbols",
        ],
        "severity": "structural",
    },
    ".htm": ".html",
    ".css": {
        "parser": "bracket_state_machine",
        "checks": ["brace_matching", "string_integrity", "comment_integrity"],
        "severity": "structural",
    },
    ".js": {
        "parser": "acorn+bracket_state_machine",
        "checks": [
            "bracket_matching",
            "string_integrity",
            "template_literal_integrity",
            "comment_integrity",
            "syntax_tree_parse",
            "scope_symbols",
        ],
        "severity": "structural",
    },
    ".ts": ".js",
    ".jsx": ".js",
    ".tsx": ".js",
    ".mjs": ".js",
    ".cjs": ".js",
    ".md": None,
    ".txt": None,
    ".sh": None,
    ".bash": None,
    ".zsh": None,
    ".env": None,
    ".gitignore": None,
    ".dockerignore": None,
    ".log": None,
    ".csv": None,
    ".ini": None,
    ".cfg": None,
    ".conf": None,
}

_SKIP_EXTENSIONS = frozenset(
    ext for ext, schema in VALIDATION_SCHEMA.items() if schema is None
)


@dataclass
class CheckResult:
    valid: bool
    errors: list[str]
    warnings: list[str]


def _check_python(content: str) -> CheckResult:
    errors: list[str] = []
    try:
        ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Python SyntaxError: {e.msg} at line {e.lineno}")
    except Exception as e:
        errors.append(f"Python parse error: {e}")
    return CheckResult(len(errors) == 0, errors, [])


def _check_json(content: str) -> CheckResult:
    errors: list[str] = []
    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON error: {e.msg} at L{e.lineno}:{e.colno}")
    return CheckResult(len(errors) == 0, errors, [])


def _check_yaml(content: str) -> CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        import yaml
        yaml.safe_load(content)
    except ImportError:
        warnings.append("PyYAML not installed — YAML syntax check skipped.")
    except Exception as e:
        errors.append(f"YAML error: {e}")
    return CheckResult(len(errors) == 0, errors, warnings)


def _check_toml(content: str) -> CheckResult:
    errors: list[str] = []
    try:
        tomllib.loads(content)
    except tomllib.TOMLDecodeError as e:
        errors.append(f"TOML error: {e}")
    except Exception as e:
        errors.append(f"TOML parse error: {e}")
    return CheckResult(len(errors) == 0, errors, [])


def _check_xml(content: str) -> CheckResult:
    errors: list[str] = []
    try:
        ET.fromstring(content)
    except Exception as e:
        errors.append(f"XML error: {e}")
    return CheckResult(len(errors) == 0, errors, [])


_VOID_ELEMENTS = frozenset([
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
])

_OPTIONAL_CLOSE_TAGS = frozenset([
    "html", "head", "body", "p", "li", "dd", "dt", "td", "th", "tr",
    "thead", "tbody", "tfoot", "option", "optgroup", "colgroup", "caption",
    "rt", "rp",
])


class HtmlTagValidator(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.errors: list[str] = []
        self._stack: list[tuple[str, tuple[int, int]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() not in _VOID_ELEMENTS:
            self._stack.append((tag.lower(), self.getpos()))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        pass

    def handle_endtag(self, tag: str) -> None:
        tag_l = tag.lower()
        pos = self.getpos()
        if tag_l in _VOID_ELEMENTS:
            self.errors.append(
                f"HTML: void element <{tag}> cannot have a closing tag </{tag}> at L{pos[0]}:{pos[1]}"
            )
            return
        if not self._stack:
            self.errors.append(f"HTML: unexpected closing tag </{tag}> at L{pos[0]}:{pos[1]}")
            return
        for i in range(len(self._stack) - 1, -1, -1):
            if self._stack[i][0] == tag_l:
                for unclosed, p in self._stack[i + 1:]:
                    if unclosed not in _OPTIONAL_CLOSE_TAGS:
                        self.errors.append(
                            f"HTML: unclosed tag <{unclosed}> opened at L{p[0]}:{p[1]} before closing </{tag}>"
                        )
                self._stack = self._stack[:i]
                return
        self.errors.append(
            f"HTML: closing tag </{tag}> has no matching opening tag at L{pos[0]}:{pos[1]}"
        )

    def finish(self) -> None:
        if self.rawdata.strip():
            raw = self.rawdata.strip().replace("\n", " ")[:50]
            if raw.startswith("<!--"):
                self.errors.append("HTML: unclosed comment starting with '<!--'")
            else:
                self.errors.append(f"HTML: malformed or unterminated syntax near '{raw}'")
        for tag, pos in self._stack:
            if tag not in _OPTIONAL_CLOSE_TAGS:
                self.errors.append(f"HTML: unclosed tag <{tag}> opened at L{pos[0]}:{pos[1]}")


_ACORN_ENV_CACHE: dict[str, str] | None = None
_ACORN_AVAILABLE_CACHE: bool | None = None


def _get_acorn_env() -> dict[str, str]:
    global _ACORN_ENV_CACHE
    if _ACORN_ENV_CACHE is not None:
        return _ACORN_ENV_CACHE
    env = os.environ.copy()
    paths: list[str] = []
    try:
        res = subprocess.run(["npm", "root", "-g"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0 and res.stdout.strip():
            paths.append(res.stdout.strip())
    except Exception:
        pass
    home_cache = os.path.expanduser("~/.cache/human-skills/acorn/node_modules")
    if os.path.isdir(home_cache):
        paths.append(home_cache)
    cur = env.get("NODE_PATH", "")
    if paths:
        extra = ":".join(paths)
        env["NODE_PATH"] = f"{extra}:{cur}" if cur else extra
    _ACORN_ENV_CACHE = env
    return env


def _missing_system_binaries() -> list[str]:
    missing: list[str] = []
    if not shutil.which("node"):
        missing.append("nodejs")
    if not shutil.which("npm"):
        missing.append("npm")
    return missing


def _build_install_commands(missing_modules: list[str], missing_binaries: list[str]) -> list[str]:
    commands: list[str] = []
    sudo_ok = subprocess.run(["sudo", "-n", "true"], capture_output=True).returncode == 0
    if sudo_ok and ("nodejs" in missing_binaries or "npm" in missing_binaries):
        commands.append("sudo apt-get update -qq && sudo apt-get install -y -qq nodejs npm")

    if "acorn" in missing_modules:
        commands.append('npm install -g acorn 2>/dev/null || npm install --prefix "$HOME/.cache/human-skills/acorn" acorn')

    return commands


def _launch_background_installer(missing_modules: list[str], missing_binaries: list[str]) -> None:
    scratch_dir = "data/scratch/validator"
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


def _ensure_acorn_available() -> bool:
    global _ACORN_AVAILABLE_CACHE
    if _ACORN_AVAILABLE_CACHE is True:
        return True

    missing_binaries = _missing_system_binaries()
    missing_modules: list[str] = []

    if shutil.which("node"):
        env = _get_acorn_env()
        try:
            res = subprocess.run(
                ["node", "-e", "require('acorn')"],
                capture_output=True,
                timeout=2,
                env=env,
            )
            if res.returncode == 0:
                _ACORN_AVAILABLE_CACHE = True
                return True
        except Exception:
            pass
        missing_modules.append("acorn")
    else:
        missing_modules.append("acorn")

    _launch_background_installer(missing_modules, missing_binaries)
    return False


_ACORN_RUNNER_SCRIPT = """
const fs = require('fs');
let acorn;
try { acorn = require('acorn'); } catch (e) { process.exit(2); }

const payload = JSON.parse(fs.readFileSync(0, 'utf-8'));
const code = payload.code;
const offset = payload.offset || 0;

const BROWSER_GLOBALS = new Set([
  'window', 'document', 'canvas', 'ctx', 'Math', 'requestAnimationFrame', 'cancelAnimationFrame',
  'performance', 'console', 'Array', 'Object', 'String', 'Number', 'Boolean', 'Symbol', 'BigInt',
  'Date', 'RegExp', 'Error', 'TypeError', 'RangeError', 'ReferenceError', 'SyntaxError',
  'Map', 'Set', 'WeakMap', 'WeakSet', 'Promise', 'JSON', 'Proxy', 'Reflect',
  'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval', 'queueMicrotask',
  'addEventListener', 'removeEventListener', 'dispatchEvent',
  'innerWidth', 'innerHeight', 'outerWidth', 'outerHeight', 'screen',
  'location', 'navigator', 'history', 'localStorage', 'sessionStorage',
  'Image', 'Audio', 'ImageData', 'Path2D', 'CanvasRenderingContext2D', 'WebGLRenderingContext',
  'HTMLElement', 'HTMLCanvasElement', 'Element', 'Node', 'Event', 'CustomEvent',
  'fetch', 'XMLHttpRequest', 'WebSocket', 'FormData', 'URL', 'URLSearchParams', 'Blob', 'File',
  'FileReader', 'Int8Array', 'Uint8Array', 'Uint8ClampedArray', 'Int16Array', 'Uint16Array',
  'Int32Array', 'Uint32Array', 'Float32Array', 'Float64Array', 'BigInt64Array', 'BigUint64Array',
  'ArrayBuffer', 'DataView', 'Atomics', 'WebAssembly',
  'NaN', 'undefined', 'Infinity', 'isNaN', 'isFinite', 'parseInt', 'parseFloat',
  'encodeURI', 'encodeURIComponent', 'decodeURI', 'decodeURIComponent'
]);

const errors = [];
const warnings = [];

let ast;
try {
  ast = acorn.parse(code, { ecmaVersion: 'latest', locations: true, sourceType: 'script' });
} catch (err) {
  const line = offset + (err.loc ? err.loc.line - 1 : 0);
  const col = err.loc ? err.loc.column + 1 : 1;
  errors.push(`JS SyntaxError at L${line}:C${col} - ${err.message}`);
}

if (ast) {
  function checkIdentifier(idNode, scope) {
    if (!idNode || idNode.type !== 'Identifier') return;
    const name = idNode.name;
    if (!scope.has(name) && !BROWSER_GLOBALS.has(name)) {
      const l = offset + idNode.loc.start.line - 1;
      const c = idNode.loc.start.column + 1;
      warnings.push(`JS ReferenceWarning at L${l}:C${c} - "${name}" is not defined`);
    }
  }

  function walk(node, scope) {
    if (!node || typeof node !== 'object') return;

    if (node.type === 'VariableDeclaration') {
      for (const d of node.declarations) {
        if (d.id && d.id.type === 'Identifier') scope.add(d.id.name);
        if (d.init) walk(d.init, scope);
      }
      return;
    }
    if (node.type === 'FunctionDeclaration') {
      if (node.id && node.id.type === 'Identifier') scope.add(node.id.name);
      const inner = new Set(scope);
      for (const p of node.params) {
        if (p.type === 'Identifier') inner.add(p.name);
      }
      walk(node.body, inner);
      return;
    }
    if (node.type === 'FunctionExpression' || node.type === 'ArrowFunctionExpression') {
      const inner = new Set(scope);
      if (node.id && node.id.type === 'Identifier') inner.add(node.id.name);
      for (const p of node.params) {
        if (p.type === 'Identifier') inner.add(p.name);
      }
      walk(node.body, inner);
      return;
    }
    if (node.type === 'CatchClause') {
      const inner = new Set(scope);
      if (node.param && node.param.type === 'Identifier') inner.add(node.param.name);
      walk(node.body, inner);
      return;
    }
    if (node.type === 'MemberExpression') {
      walk(node.object, scope);
      if (node.computed) walk(node.property, scope);
      return;
    }
    if (node.type === 'Property') {
      if (node.computed) walk(node.key, scope);
      walk(node.value, scope);
      return;
    }
    if (node.type === 'Identifier') {
      checkIdentifier(node, scope);
      return;
    }

    for (const k of Object.keys(node)) {
      if (k === 'loc' || k === 'range') continue;
      const child = node[k];
      if (Array.isArray(child)) {
        for (const item of child) walk(item, scope);
      } else if (child && typeof child === 'object') {
        walk(child, scope);
      }
    }
  }

  walk(ast, new Set());
}

console.log(JSON.stringify({ errors, warnings }));
"""


def _run_acorn_validation(code: str, offset: int = 0) -> tuple[list[str], list[str]]:
    if not _ensure_acorn_available():
        return [], ["Acorn parser not detected — background installation launched (data/scratch/validator/installer.log). It will activate automatically."]
    env = _get_acorn_env()
    payload = json.dumps({"code": code, "offset": offset})
    try:
        res = subprocess.run(
            ["node", "-e", _ACORN_RUNNER_SCRIPT],
            input=payload,
            capture_output=True,
            text=True,
            env=env,
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            parsed = json.loads(res.stdout.strip())
            return parsed.get("errors", []), parsed.get("warnings", [])
    except Exception as e:
        return [f"Acorn validation execution error: {e}"], []
    return [], []


def _check_html(content: str) -> CheckResult:
    errors: list[str] = []
    warnings: list[str] = []
    validator = HtmlTagValidator()
    try:
        validator.feed(content)
    except Exception as e:
        errors.append(f"HTML parse error: {e}")
    validator.finish()
    validator.close()
    errors.extend(validator.errors)

    pattern = re.compile(r"<script(?:\s+[^>]*)?>([\s\S]*?)</script>", re.IGNORECASE)
    for match in pattern.finditer(content):
        script_code = match.group(1)
        if not script_code.strip():
            continue
        offset = content[:match.start(1)].count("\n") + 1
        script_errors, script_warnings = _run_acorn_validation(script_code, offset)
        errors.extend(script_errors)
        warnings.extend(script_warnings)

    return CheckResult(len(errors) == 0, errors, warnings)


def _skip_block_comment(content: str, i: int, n: int, line: int, lang: str) -> tuple[int, int, str | None]:
    start_line = line
    i += 2
    while i < n:
        if content[i] == "\n":
            line += 1
        elif content[i] == "*" and i + 1 < n and content[i + 1] == "/":
            return i + 2, line, None
        i += 1
    return n, line, f"{lang}: unclosed comment starting at L{start_line}"


def _skip_css_string(content: str, i: int, n: int, line: int, quote: str) -> tuple[int, int, str | None]:
    start_line = line
    i += 1
    while i < n:
        if content[i] == "\\":
            i += 2
            continue
        if content[i] == "\n":
            line += 1
            i += 1
            continue
        if content[i] == quote:
            return i + 1, line, None
        i += 1
    return n, line, f"CSS: unclosed string starting at L{start_line}"


def _check_css(content: str) -> CheckResult:
    errors: list[str] = []
    brace_stack: list[int] = []
    i = 0
    line = 1
    n = len(content)

    while i < n:
        ch = content[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch == "/" and i + 1 < n and content[i + 1] == "*":
            i, line, err = _skip_block_comment(content, i, n, line, "CSS")
            if err:
                errors.append(err)
            continue
        if ch in ('"', "'"):
            i, line, err = _skip_css_string(content, i, n, line, ch)
            if err:
                errors.append(err)
            continue
        if ch == "{":
            brace_stack.append(line)
            i += 1
            continue
        if ch == "}":
            if not brace_stack:
                errors.append(f"CSS: unexpected '}}' at L{line}")
            else:
                brace_stack.pop()
            i += 1
            continue
        i += 1

    for open_line in brace_stack:
        errors.append(f"CSS: unclosed '{{' opened at L{open_line}")

    return CheckResult(len(errors) == 0, errors, [])


_JS_BRACKET_PAIRS: dict[str, str] = {")": "(", "]": "[", "}": "{"}


def _skip_js_line_comment(content: str, i: int, n: int) -> int:
    i += 2
    while i < n and content[i] != "\n":
        i += 1
    return i


def _skip_js_comments(content: str, i: int, n: int, line: int) -> tuple[int, int, str | None]:
    if content[i + 1] == "/":
        return _skip_js_line_comment(content, i, n), line, None
    if content[i + 1] == "*":
        return _skip_block_comment(content, i, n, line, "JS")
    return i + 1, line, None


def _skip_js_template_literal(content: str, i: int, n: int, line: int) -> tuple[int, int, str | None]:
    start_line = line
    i += 1
    while i < n:
        if content[i] == "\\":
            i += 2
            continue
        if content[i] == "\n":
            line += 1
            i += 1
            continue
        if content[i] == "`":
            return i + 1, line, None
        i += 1
    return n, line, f"JS: unclosed template literal starting at L{start_line}"


def _skip_js_string(content: str, i: int, n: int, line: int, quote: str) -> tuple[int, int, str | None]:
    start_line = line
    i += 1
    while i < n:
        if content[i] == "\\":
            i += 2
            continue
        if content[i] == "\n":
            return i, line, f"JS: unterminated string at L{start_line}"
        if content[i] == quote:
            return i + 1, line, None
        i += 1
    return n, line, f"JS: unclosed string starting at L{start_line}"


def _pop_matching_bracket(stack: list[tuple[str, int]], ch: str, line: int) -> list[str]:
    expected_open = _JS_BRACKET_PAIRS[ch]
    if not stack:
        return [f"JS: unexpected '{ch}' at L{line}"]
    for idx in range(len(stack) - 1, -1, -1):
        if stack[idx][0] == expected_open:
            errs = [
                f"JS: unclosed '{stack[j][0]}' opened at L{stack[j][1]}"
                for j in range(len(stack) - 1, idx, -1)
            ]
            del stack[idx:]
            return errs
    return [f"JS: unexpected '{ch}' at L{line}"]


def _handle_js_bracket(stack: list[tuple[str, int]], ch: str, line: int) -> list[str]:
    if ch in "([{":
        stack.append((ch, line))
        return []
    return _pop_matching_bracket(stack, ch, line)


def _scan_js_tokens(content: str) -> tuple[list[str], list[tuple[str, int]]]:
    errors: list[str] = []
    stack: list[tuple[str, int]] = []
    i = 0
    line = 1
    n = len(content)

    while i < n:
        ch = content[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch == "/" and i + 1 < n and content[i + 1] in "/*":
            i, line, err = _skip_js_comments(content, i, n, line)
            if err:
                errors.append(err)
            continue
        if ch == "`":
            i, line, err = _skip_js_template_literal(content, i, n, line)
            if err:
                errors.append(err)
            continue
        if ch in ('"', "'"):
            i, line, err = _skip_js_string(content, i, n, line, ch)
            if err:
                errors.append(err)
            continue
        if ch in "([{)]}":
            errors.extend(_handle_js_bracket(stack, ch, line))
            i += 1
            continue
        i += 1

    return errors, stack


def _check_js(content: str) -> CheckResult:
    errors, stack = _scan_js_tokens(content)
    for bracket, open_line in stack:
        errors.append(f"JS: unclosed '{bracket}' opened at L{open_line}")
    acorn_errors, acorn_warnings = _run_acorn_validation(content, offset=1)
    for err in acorn_errors:
        if err not in errors:
            errors.append(err)
    return CheckResult(len(errors) == 0, errors, acorn_warnings)


CheckerFunc = Callable[[str], CheckResult]

_CHECKERS: dict[str, CheckerFunc] = {
    ".py": _check_python,
    ".json": _check_json,
    ".yaml": _check_yaml,
    ".yml": _check_yaml,
    ".toml": _check_toml,
    ".xml": _check_xml,
    ".svg": _check_xml,
    ".xhtml": _check_xml,
    ".html": _check_html,
    ".htm": _check_html,
    ".css": _check_css,
    ".js": _check_js,
    ".ts": _check_js,
    ".jsx": _check_js,
    ".tsx": _check_js,
    ".mjs": _check_js,
    ".cjs": _check_js,
}


def _extract_extension(target_file: str) -> str:
    cleaned = target_file.strip().replace("\\", "/")
    filename = cleaned.rsplit("/", 1)[-1]
    if filename.startswith(".") and filename.count(".") == 1:
        return filename.lower()
    dot_idx = filename.rfind(".")
    if dot_idx != -1:
        return filename[dot_idx:].lower()
    return ""


def validate_syntax(content: str, target_file: str) -> CheckResult:
    if not content.strip():
        return CheckResult(True, [], [])
    ext = _extract_extension(target_file)
    if ext in _SKIP_EXTENSIONS:
        return CheckResult(True, [], [])
    checker = _CHECKERS.get(ext)
    if not checker:
        return CheckResult(True, [], [f"No syntax checker for '{ext}' files — skipped."])
    return checker(content)
