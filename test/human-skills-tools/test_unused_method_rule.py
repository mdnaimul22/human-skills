import ast
import sys
from pathlib import Path
import pytest

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_LINTER_DIR = _PROJECT_ROOT / "skills" / "storage" / "my_skills" / "architecture-auditing-linter" / "scripts"
if str(_LINTER_DIR) not in sys.path:
    sys.path.insert(0, str(_LINTER_DIR))

from default.base import FileContext
from default.unused_dependencies import UDBDPlugin, UDBDMethodRule


def test_unused_method_detected():
    code = """
class OrderService:
    def place_order(self):
        self._validate_cart()

    def _validate_cart(self):
        return True

    def _obsolete_tax_calc(self):
        return 0
"""
    tree = ast.parse(code)
    ctx = FileContext(Path("src/services/order.py"), Path("src"), set(), code)
    rule = UDBDMethodRule(ctx)
    violations, advisories = rule.run(tree)
    assert len(violations) == 1
    assert "_obsolete_tax_calc" in violations[0]
    assert "[Dead Code Violation]" in violations[0]


def test_used_methods_ignored():
    code = """
class Worker:
    def __init__(self):
        self.handler = self._callback

    def _callback(self):
        pass

    async def _async_step(self):
        return 1

    async def run(self):
        await self._async_step()
"""
    tree = ast.parse(code)
    ctx = FileContext(Path("src/core/worker.py"), Path("src"), set(), code)
    rule = UDBDMethodRule(ctx)
    violations, advisories = rule.run(tree)
    assert len(violations) == 0


def test_udbd_standalone_api():
    plugin = UDBDPlugin()
    code = """
class Sample:
    def _dead(self):
        pass
"""
    res = plugin.analyze_source(code, "test_file.py")
    assert len(res["unused_methods"]) == 1
    assert res["unused_methods"][0]["method_name"] == "_dead"
    assert res["unused_methods"][0]["class_name"] == "Sample"


def test_test_file_skipped():
    code = """
class TestSuite:
    def _test_helper(self):
        pass
"""
    tree = ast.parse(code)
    ctx = FileContext(Path("tests/test_service.py"), Path("tests"), set(), code)
    rule = UDBDMethodRule(ctx)
    violations, advisories = rule.run(tree)
    assert len(violations) == 0

