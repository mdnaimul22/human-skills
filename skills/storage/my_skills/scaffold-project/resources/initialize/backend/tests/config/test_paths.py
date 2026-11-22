import pytest
import sys
from pathlib import Path
from src.config.paths import PROJECT_ROOT, ProjectBoundary


def test_project_boundary_detect() -> None:
    assert isinstance(PROJECT_ROOT, ProjectBoundary)
    assert isinstance(PROJECT_ROOT, Path)
    assert PROJECT_ROOT.exists()
    assert PROJECT_ROOT.is_dir()
    assert (PROJECT_ROOT / "pyproject.toml").exists() or (PROJECT_ROOT / ".git").exists()


def test_safe_resolve_valid_paths() -> None:
    resolved_file = PROJECT_ROOT.safe_resolve("pyproject.toml")
    assert resolved_file.is_file()
    assert resolved_file.name == "pyproject.toml"

    resolved_abs = PROJECT_ROOT.safe_resolve(str(PROJECT_ROOT / "pyproject.toml"))
    assert resolved_abs == resolved_file


def test_safe_resolve_traversal_blocked() -> None:
    with pytest.raises(ValueError, match="escapes sandbox"):
        PROJECT_ROOT.safe_resolve("../../etc/passwd")

    with pytest.raises(ValueError, match="escapes sandbox"):
        PROJECT_ROOT.safe_resolve("/etc/shadow")


def test_safe_resolve_null_bytes_and_empty() -> None:
    with pytest.raises(ValueError, match="Path cannot be empty or whitespace"):
        PROJECT_ROOT.safe_resolve("")

    with pytest.raises(ValueError, match="Path cannot be empty or whitespace"):
        PROJECT_ROOT.safe_resolve("   ")

    with pytest.raises(ValueError, match="Null bytes not permitted"):
        PROJECT_ROOT.safe_resolve("src/sample\0evil.txt")


def test_path_operators_and_interoperability() -> None:
    sub = PROJECT_ROOT / "src"
    assert isinstance(sub, Path)
    assert str(sub) == f"{PROJECT_ROOT}/src"
    assert PROJECT_ROOT.resolve() == PROJECT_ROOT
    assert str(PROJECT_ROOT) in sys.path
