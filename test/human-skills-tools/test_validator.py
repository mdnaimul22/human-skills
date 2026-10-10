import sys
from pathlib import Path
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "skills") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "skills"))

from helpers.validator import validate_syntax, CheckResult, VALIDATION_SCHEMA


def test_python_valid_syntax():
    res = validate_syntax("x: int = 1\nprint(x)\n", "app.py")
    assert res.valid is True
    assert len(res.errors) == 0


def test_python_invalid_syntax():
    res = validate_syntax("def foo(:\n", "app.py")
    assert res.valid is False
    assert any("syntaxerror" in e.lower() for e in res.errors)


def test_python_indentation_error():
    res = validate_syntax("def foo():\nx = 1\n", "app.py")
    assert res.valid is False


def test_json_valid():
    res = validate_syntax('{"key": "value", "list": [1, 2]}', "data.json")
    assert res.valid is True


def test_json_invalid():
    res = validate_syntax('{key: "value"}', "data.json")
    assert res.valid is False
    assert any("json" in e.lower() for e in res.errors)


def test_json_trailing_comma():
    res = validate_syntax('{"a": 1,}', "data.json")
    assert res.valid is False


def test_yaml_valid():
    res = validate_syntax("server:\n  port: 8080\n", "config.yaml")
    assert res.valid is True


def test_yaml_invalid():
    res = validate_syntax("server:\n  port: 8080\n bad_indent", "config.yml")
    assert res.valid is False


def test_toml_valid():
    res = validate_syntax('[section]\nname = "test"\n', "config.toml")
    assert res.valid is True


def test_toml_invalid():
    res = validate_syntax('[section\nname = "test"\n', "config.toml")
    assert res.valid is False
    assert any("toml" in e.lower() for e in res.errors)


def test_xml_valid():
    res = validate_syntax("<root><child attr='1'/></root>", "data.xml")
    assert res.valid is True


def test_xml_mismatched_tags():
    res = validate_syntax("<root><child></root>", "data.xml")
    assert res.valid is False


def test_svg_xml_alias():
    res_valid = validate_syntax("<svg viewBox='0 0 10 10'><circle/></svg>", "icon.svg")
    assert res_valid.valid is True

    res_invalid = validate_syntax("<svg><circle></svg>", "icon.svg")
    assert res_invalid.valid is False


def test_html_valid():
    content = "<!DOCTYPE html><html><head><title>T</title></head><body><h1>H</h1><br><img src='a.png'></body></html>"
    res = validate_syntax(content, "index.html")
    assert res.valid is True


def test_html_unclosed_tag():
    res = validate_syntax("<div><span>content</div>", "page.html")
    assert res.valid is False
    assert any("closing tag </div" in e.lower() or "unclosed" in e.lower() for e in res.errors)


def test_html_void_elements_allowed():
    res = validate_syntax("<p>Line 1<br>Line 2<hr><input type='text'></p>", "page.htm")
    assert res.valid is True


def test_html_optional_closing_tags():
    res = validate_syntax("<ul><li>Item 1<li>Item 2</ul>", "list.html")
    assert res.valid is True


def test_css_valid():
    content = "body { margin: 0; padding: 0; } @media (max-width: 600px) { body { font-size: 14px; } }"
    res = validate_syntax(content, "style.css")
    assert res.valid is True


def test_css_unclosed_brace():
    res = validate_syntax("body { margin: 0;", "style.css")
    assert res.valid is False
    assert any("unclosed '{'" in e for e in res.errors)


def test_css_extra_closing_brace():
    res = validate_syntax("body { margin: 0; } }", "style.css")
    assert res.valid is False
    assert any("unexpected '}'" in e for e in res.errors)


def test_css_comments_and_strings():
    content = "/* comment */ .icon::before { content: '}'; }"
    res = validate_syntax(content, "style.css")
    assert res.valid is True


def test_js_valid():
    content = "function add(a, b) { return a + b; }\nconsole.log(add(1, 2));\n"
    res = validate_syntax(content, "app.js")
    assert res.valid is True


def test_js_unclosed_bracket():
    res = validate_syntax("const arr = [1, 2, 3;", "app.js")
    assert res.valid is False
    assert any("unclosed '['" in e for e in res.errors)


def test_js_unclosed_template_literal():
    res = validate_syntax("const s = `hello world;", "app.ts")
    assert res.valid is False
    assert any("unclosed template literal" in e for e in res.errors)


def test_js_unclosed_comment():
    res = validate_syntax("/* comment started\nconst x = 1;", "app.jsx")
    assert res.valid is False
    assert any("unclosed comment" in e for e in res.errors)


def test_skip_extensions():
    for ext in [".md", ".txt", ".sh", ".env", ".gitignore", ".log"]:
        res = validate_syntax("random unformatted content", f"file{ext}")
        assert res.valid is True
        assert len(res.warnings) == 0


def test_unknown_extension_warns():
    res = validate_syntax("binary or unknown payload", "file.unknown_xyz")
    assert res.valid is True
    assert len(res.warnings) == 1
    assert "No syntax checker" in res.warnings[0]


def test_empty_content():
    assert validate_syntax("", "app.py").valid is True
    assert validate_syntax("   \n\t  ", "index.html").valid is True
