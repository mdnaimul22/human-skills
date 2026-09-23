import os
import sys
import json
import subprocess
from pathlib import Path
import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "skills" / "storage" / "my_skills" / "human-skills-tools" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import skills.helpers.paths

from find_by_name import FindByName
from grep_search import GrepSearch
from list_dir import ListDir
from view_file import ViewFile
from write_to_file import WriteToFile
from skills.helpers.execute import dispatch


@pytest.mark.asyncio
async def test_find_by_name_pattern(tmp_path):
    (tmp_path / "app.py").write_text("print(1)")
    (tmp_path / "util.py").write_text("print(2)")
    (tmp_path / "notes.txt").write_text("hello")

    tool = FindByName(args={"search_directory": str(tmp_path), "pattern": "*.py"})
    res = await tool.execute()

    assert "Found 2 result(s)" in res.message
    assert "app.py" in res.message
    assert "util.py" in res.message
    assert "notes.txt" not in res.message


@pytest.mark.asyncio
async def test_find_by_name_type_filter(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    (tmp_path / "sample.txt").write_text("data")

    tool = FindByName(args={"search_directory": str(tmp_path), "type": "directory"})
    res = await tool.execute()

    assert "subdir/ (directory)" in res.message
    assert "sample.txt" not in res.message


@pytest.mark.asyncio
async def test_find_by_name_max_depth(tmp_path):
    level1 = tmp_path / "lvl1"
    level1.mkdir()
    (tmp_path / "file1.txt").write_text("1")
    (level1 / "file2.txt").write_text("2")

    tool = FindByName(args={"search_directory": str(tmp_path), "pattern": "*.txt", "max_depth": "1"})
    res = await tool.execute()

    assert "file1.txt" in res.message
    assert "file2.txt" not in res.message


@pytest.mark.asyncio
async def test_find_by_name_excludes(tmp_path):
    ignored = tmp_path / "ignored"
    ignored.mkdir()
    (ignored / "bad.py").write_text("print(0)")
    (tmp_path / "good.py").write_text("print(1)")

    tool = FindByName(args={"search_directory": str(tmp_path), "pattern": "*.py", "excludes": "ignored"})
    res = await tool.execute()

    assert "good.py" in res.message
    assert "bad.py" not in res.message


@pytest.mark.asyncio
async def test_find_by_name_missing_directory():
    tool = FindByName(args={})
    res = await tool.execute()
    assert "Error: 'search_directory' is required" in res.message


@pytest.mark.asyncio
async def test_grep_search_basic(tmp_path):
    target = tmp_path / "service.py"
    target.write_text("def fetch_user():\n    return 'user'\n")

    tool = GrepSearch(args={"search_path": str(tmp_path), "query": "fetch_user", "match_per_line": "true"})
    res = await tool.execute()

    assert "Found 1 match(es)" in res.message
    assert "service.py" in res.message
    assert "def fetch_user" in res.message


@pytest.mark.asyncio
async def test_grep_search_ast_detection(tmp_path):
    code = "async def authenticate():\n    return 'secret_token'\n"
    (tmp_path / "auth.py").write_text(code)

    tool = GrepSearch(args={"search_path": str(tmp_path), "query": "secret_token", "match_per_line": "true"})
    res = await tool.execute()

    assert "[async_function: authenticate]" in res.message


@pytest.mark.asyncio
async def test_grep_search_case_insensitive(tmp_path):
    (tmp_path / "doc.txt").write_text("ERROR: failed to connect\n")

    tool_sensitive = GrepSearch(args={"search_path": str(tmp_path), "query": "error", "case_insensitive": "false"})
    res_sensitive = await tool_sensitive.execute()
    assert "No matches found" in res_sensitive.message

    tool_insensitive = GrepSearch(args={"search_path": str(tmp_path), "query": "error", "case_insensitive": "true"})
    res_insensitive = await tool_insensitive.execute()
    assert "Found 1 match(es)" in res_insensitive.message


@pytest.mark.asyncio
async def test_grep_search_filenames_only(tmp_path):
    (tmp_path / "a.py").write_text("target_token = 1\n")
    (tmp_path / "b.py").write_text("target_token = 2\n")

    tool = GrepSearch(args={"search_path": str(tmp_path), "query": "target_token", "match_per_line": "false"})
    res = await tool.execute()

    assert "Found 2 match(es)" in res.message
    assert "a.py" in res.message
    assert "b.py" in res.message
    assert "L1:" not in res.message


@pytest.mark.asyncio
async def test_grep_search_includes(tmp_path):
    (tmp_path / "file.py").write_text("TOKEN = 1\n")
    (tmp_path / "file.json").write_text('{"TOKEN": 1}\n')

    tool = GrepSearch(args={"search_path": str(tmp_path), "query": "TOKEN", "includes": "*.py"})
    res = await tool.execute()

    assert "file.py" in res.message
    assert "file.json" not in res.message


@pytest.mark.asyncio
async def test_grep_search_missing_query():
    tool = GrepSearch(args={})
    res = await tool.execute()
    assert "Error: 'query' is required" in res.message


@pytest.mark.asyncio
async def test_list_dir_table_output(tmp_path):
    (tmp_path / "test_file.txt").write_text("sample content")
    sub = tmp_path / "nested_dir"
    sub.mkdir()
    (sub / "inner.txt").write_text("inner")

    tool = ListDir(args={"directory_path": str(tmp_path)})
    res = await tool.execute()

    assert "| Name | Type | Size | Modified | Permissions |" in res.message
    assert "| nested_dir/ | Dir |" in res.message
    assert "| test_file.txt | File |" in res.message


@pytest.mark.asyncio
async def test_list_dir_empty_directory(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()

    tool = ListDir(args={"directory_path": str(empty)})
    res = await tool.execute()

    assert f"Directory '{empty}' is empty." in res.message


@pytest.mark.asyncio
async def test_list_dir_nonexistent():
    tool = ListDir(args={"directory_path": "/path/does/not/exist_12345"})
    res = await tool.execute()
    assert "not a valid directory" in res.message


@pytest.mark.asyncio
async def test_list_dir_missing_arg():
    tool = ListDir(args={})
    res = await tool.execute()
    assert "Error: 'directory_path' is required" in res.message


@pytest.mark.asyncio
async def test_view_file_full(tmp_path):
    target = tmp_path / "test.py"
    target.write_text("line_one\nline_two\nline_three\n")

    tool = ViewFile(args={"absolute_path": str(target)})
    res = await tool.execute()

    assert f"File: {target}" in res.message
    assert "Total lines: 3" in res.message
    assert "1: line_one" in res.message
    assert "2: line_two" in res.message
    assert "3: line_three" in res.message


@pytest.mark.asyncio
async def test_view_file_range(tmp_path):
    target = tmp_path / "test.py"
    target.write_text("1\n2\n3\n4\n5\n")

    tool = ViewFile(args={"absolute_path": str(target), "start_line": "2", "end_line": "4"})
    res = await tool.execute()

    assert "Showing: L2–L4" in res.message
    assert "2: 2" in res.message
    assert "3: 3" in res.message
    assert "4: 4" in res.message
    assert "1: 1" not in res.message
    assert "5: 5" not in res.message


@pytest.mark.asyncio
async def test_view_file_empty(tmp_path):
    target = tmp_path / "empty.txt"
    target.write_text("")

    tool = ViewFile(args={"absolute_path": str(target)})
    res = await tool.execute()
    assert res.message == "(empty file)"


@pytest.mark.asyncio
async def test_view_file_nonexistent():
    tool = ViewFile(args={"absolute_path": "/nonexistent/path/here.py"})
    res = await tool.execute()
    assert "not found" in res.message


@pytest.mark.asyncio
async def test_view_file_missing_arg():
    tool = ViewFile(args={})
    res = await tool.execute()
    assert "Error: 'absolute_path' is required" in res.message


@pytest.mark.asyncio
async def test_write_to_file_create_python(tmp_path):
    target = tmp_path / "valid.py"
    content = "x: int = 10\ny: int = 20\n"

    tool = WriteToFile(args={"target_file": str(target), "code_content": content, "auto_check": "true", "strict_mode": "true"})
    res = await tool.execute()

    assert "File created:" in res.message
    assert "Syntax  : ✓ passed" in res.message
    assert target.exists()
    assert target.read_text() == content


@pytest.mark.asyncio
async def test_write_to_file_no_overwrite(tmp_path):
    target = tmp_path / "existing.py"
    target.write_text("a = 1")

    tool = WriteToFile(args={"target_file": str(target), "code_content": "a = 2", "overwrite": "false"})
    res = await tool.execute()

    assert "already exists" in res.message
    assert target.read_text() == "a = 1"


@pytest.mark.asyncio
async def test_write_to_file_with_overwrite(tmp_path):
    target = tmp_path / "existing.py"
    target.write_text("a = 1")

    tool = WriteToFile(args={"target_file": str(target), "code_content": "a = 2\n", "overwrite": "true"})
    res = await tool.execute()

    assert "File created:" in res.message
    assert target.read_text() == "a = 2\n"


@pytest.mark.asyncio
async def test_write_to_file_syntax_error_strict(tmp_path):
    target = tmp_path / "broken.py"
    content = "def incomplete_func("

    tool = WriteToFile(args={"target_file": str(target), "code_content": content, "strict_mode": "true"})
    res = await tool.execute()

    assert "Syntax validation failed" in res.message
    assert not target.exists()


@pytest.mark.asyncio
async def test_write_to_file_auto_mkdir(tmp_path):
    target = tmp_path / "deep" / "nested" / "script.py"
    content = "val = 42\n"

    tool = WriteToFile(args={"target_file": str(target), "code_content": content})
    res = await tool.execute()

    assert "File created:" in res.message
    assert target.exists()
    assert target.read_text() == content


@pytest.mark.asyncio
async def test_write_to_file_missing_arg():
    tool = WriteToFile(args={})
    res = await tool.execute()
    assert "Error: 'target_file' is required" in res.message


def test_dispatch_integration(tmp_path):
    test_file = tmp_path / "dispatch_test.py"
    code = "def add(a: int, b: int) -> int:\n    return a + b\n"

    res_write = dispatch({
        "tool_name": "write_to_file",
        "tool_args": {
            "target_file": str(test_file),
            "code_content": code,
            "overwrite": "true",
        }
    })
    assert "File created:" in res_write

    res_list = dispatch({
        "tool_name": "list_dir",
        "tool_args": {
            "directory_path": str(tmp_path),
        }
    })
    assert "dispatch_test.py" in res_list

    res_view = dispatch({
        "tool_name": "view_file",
        "tool_args": {
            "absolute_path": str(test_file),
            "start_line": "1",
            "end_line": "2",
        }
    })
    assert "1: def add(a: int, b: int) -> int:" in res_view

    res_find = dispatch({
        "tool_name": "find_by_name",
        "tool_args": {
            "search_directory": str(tmp_path),
            "pattern": "*.py",
        }
    })
    assert "dispatch_test.py" in res_find

    res_grep = dispatch({
        "tool_name": "grep_search",
        "tool_args": {
            "search_path": str(tmp_path),
            "query": "def add",
            "match_per_line": "true",
        }
    })
    assert "Found 1 match(es)" in res_grep


def test_cli_integration(tmp_path):
    test_file = tmp_path / "cli_test.txt"
    payload = json.dumps({
        "tool_name": "write_to_file",
        "tool_args": {
            "target_file": str(test_file),
            "code_content": "cli test payload",
            "overwrite": "true",
        }
    })
    run = subprocess.run(
        ["human-skills", payload],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0
    assert "File created:" in run.stdout
    assert test_file.exists()
