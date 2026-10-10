import ast
import json
import tomllib
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import Callable, TypedDict


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
        "parser": "html.parser.HTMLParser",
        "checks": [
            "tag_matching",
            "void_element_rules",
            "unclosed_tags",
            "malformed_syntax",
            "comment_integrity",
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
        "parser": "bracket_state_machine",
        "checks": [
            "bracket_matching",
            "string_integrity",
            "template_literal_integrity",
            "comment_integrity",
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


def _check_html(content: str) -> CheckResult:
    errors: list[str] = []
    validator = HtmlTagValidator()
    try:
        validator.feed(content)
    except Exception as e:
        errors.append(f"HTML parse error: {e}")
    validator.finish()
    validator.close()
    errors.extend(validator.errors)
    return CheckResult(len(errors) == 0, errors, [])


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
    return CheckResult(len(errors) == 0, errors, [])


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
