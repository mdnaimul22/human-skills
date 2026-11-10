import json
import sys
from pathlib import Path
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from skills.helpers.tool import ToolStatus, Response
from skills.helpers.execute import (
    DispatchPhase,
    DispatchResult,
    dispatch,
    dispatch_with_status,
    dispatch_structured,
    _build_registry,
)


def test_tool_status_enum():
    assert ToolStatus.SUCCESS.value == "success"
    assert ToolStatus.VALIDATION_ERROR.value == "validation_error"
    assert ToolStatus.EXECUTION_ERROR.value == "execution_error"
    assert ToolStatus.NOT_FOUND.value == "not_found"
    assert ToolStatus.CRASHED.value == "crashed"


def test_response_backward_compatibility():
    res = Response(message="Old style", break_loop=True, success=True)
    assert res.message == "Old style"
    assert res.break_loop is True
    assert res.success is True
    assert res.status == ToolStatus.SUCCESS

    res_fail = Response(message="Failure", success=False)
    assert res_fail.success is False
    assert res_fail.status == ToolStatus.EXECUTION_ERROR


def test_response_to_dict():
    res = Response(
        message="Done",
        additional={"count": 5},
        status=ToolStatus.SUCCESS,
        duration_ms=12.5,
    )
    d = res.to_dict()
    assert d["status"] == "success"
    assert d["success"] is True
    assert d["message"] == "Done"
    assert d["additional"]["count"] == 5
    assert d["duration_ms"] == 12.5


def test_dispatch_structured_missing_tool():
    res = dispatch_structured({})
    assert res.status == ToolStatus.VALIDATION_ERROR.value
    assert res.phase == DispatchPhase.VALIDATING
    assert res.error_code == "MISSING_TOOL_NAME"


def test_dispatch_structured_invalid_args():
    res = dispatch_structured({"tool_name": "list_dir", "tool_args": "not-a-dict"})
    assert res.status == ToolStatus.VALIDATION_ERROR.value
    assert res.phase == DispatchPhase.VALIDATING
    assert res.error_code == "INVALID_TOOL_ARGS"


def test_dispatch_structured_unknown_tool():
    res = dispatch_structured({"tool_name": "non_existent_tool_xyz"})
    assert res.status == ToolStatus.NOT_FOUND.value
    assert res.phase == DispatchPhase.RESOLVING
    assert res.error_code == "UNKNOWN_TOOL"


def test_dispatch_structured_success():
    res = dispatch_structured({
        "tool_name": "list_dir",
        "tool_args": {"directory_path": "skills/helpers"},
    })
    assert res.status == ToolStatus.SUCCESS.value
    assert res.phase == DispatchPhase.COMPLETED
    assert "execute.py" in res.message
    assert res.duration_ms >= 0


def test_dispatch_text_mode_returns_string():
    msg, ok = dispatch_with_status({
        "tool_name": "list_dir",
        "tool_args": {"directory_path": "skills/helpers"},
    })
    assert isinstance(msg, str)
    assert ok is True
    assert "Contents of `skills/helpers`" in msg


def test_dispatch_json_mode_returns_valid_json():
    json_str, ok = dispatch_with_status({
        "tool_name": "list_dir",
        "tool_args": {"directory_path": "skills/helpers", "output_format": "json"},
    })
    assert ok is True
    parsed = json.loads(json_str)
    assert parsed["status"] == "success"
    assert parsed["phase"] == "completed"
    assert parsed["tool_name"] == "list_dir"
    assert "Contents of `skills/helpers`" in parsed["message"]


def test_registry_cache_is_fast():
    r1 = _build_registry()
    r2 = _build_registry()
    assert r1 is r2
