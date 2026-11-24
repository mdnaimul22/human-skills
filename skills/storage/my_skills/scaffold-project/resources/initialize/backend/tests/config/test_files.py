import uuid
import pytest
from pathlib import Path
from src.config.paths import PROJECT_ROOT
from src.config.files import (
    read_text,
    write_text,
    read_bytes,
    write_bytes,
    read_json,
    write_json,
    read_yaml,
    write_yaml,
    read_pickle,
    write_pickle,
    exists,
    is_file,
    is_dir,
    ensure_dir,
    delete,
    list_files,
    get_size,
    get_mtime,
    read_from_pos,
    get_abs_path,
    is_subpath,
    get_rel_path,
    sys_exists,
    sys_is_file,
    sys_is_dir,
    sys_list_dir,
    sys_read_text,
    sys_read_bytes,
)


@pytest.fixture
def tmp_workspace():
    test_id = f"test_files_{uuid.uuid4().hex[:8]}"
    rel_dir = f"data/test_tmp_{test_id}"
    ensure_dir(rel_dir)
    yield rel_dir
    delete(rel_dir)


def test_read_write_text_and_bytes(tmp_workspace: str) -> None:
    rel_txt = f"{tmp_workspace}/hello.txt"
    write_text(rel_txt, "Hello World 🚀")
    assert exists(rel_txt)
    assert is_file(rel_txt)
    assert read_text(rel_txt) == "Hello World 🚀"

    rel_bin = f"{tmp_workspace}/binary.dat"
    write_bytes(rel_bin, b"\x00\x01\x02\xff")
    assert read_bytes(rel_bin) == b"\x00\x01\x02\xff"


def test_read_write_json_and_yaml(tmp_workspace: str) -> None:
    rel_json = f"{tmp_workspace}/data.json"
    payload = {"service": "scaffold", "count": 42, "active": True}
    write_json(rel_json, payload)
    assert read_json(rel_json) == payload

    rel_yaml = f"{tmp_workspace}/config.yaml"
    write_yaml(rel_yaml, payload)
    assert read_yaml(rel_yaml) == payload


def test_read_write_pickle(tmp_workspace: str) -> None:
    rel_pkl = f"{tmp_workspace}/cache.pkl"
    sample_set = {"apple", "banana", "cherry"}
    write_pickle(sample_set, rel_pkl)
    assert read_pickle(rel_pkl) == sample_set


def test_ensure_dir_and_delete(tmp_workspace: str) -> None:
    sub_dir = f"{tmp_workspace}/nested/deep/folder"
    created = ensure_dir(sub_dir)
    assert created.exists()
    assert is_dir(sub_dir)

    delete(f"{tmp_workspace}/nested")
    assert not exists(f"{tmp_workspace}/nested")


def test_list_files(tmp_workspace: str) -> None:
    write_text(f"{tmp_workspace}/a.txt", "a")
    write_text(f"{tmp_workspace}/b.txt", "b")
    write_text(f"{tmp_workspace}/c.json", "{}")

    txt_files = list_files(tmp_workspace, "*.txt")
    names = [p.name for p in txt_files]
    assert sorted(names) == ["a.txt", "b.txt"]


def test_get_size_mtime_read_from_pos(tmp_workspace: str) -> None:
    rel_file = f"{tmp_workspace}/stream.txt"
    write_text(rel_file, "Line 1\nLine 2\n")

    assert get_size(rel_file) > 0
    assert get_mtime(rel_file) > 0

    chunk1, pos1 = read_from_pos(rel_file, 0)
    assert chunk1 == "Line 1\nLine 2\n"
    assert pos1 > 0

    chunk2, pos2 = read_from_pos(rel_file, pos1)
    assert chunk2 == ""
    assert pos2 == pos1


def test_subpath_and_rel_path(tmp_workspace: str) -> None:
    abs_str = get_abs_path(tmp_workspace)
    assert abs_str.startswith(str(PROJECT_ROOT))

    assert is_subpath(tmp_workspace, f"{tmp_workspace}/sub/file.txt")
    assert not is_subpath(f"{tmp_workspace}/sub", tmp_workspace)

    assert get_rel_path(f"{tmp_workspace}/child.txt") == f"{tmp_workspace}/child.txt"
    assert get_rel_path(get_abs_path(f"{tmp_workspace}/child.txt")) == f"{tmp_workspace}/child.txt"


def test_sandbox_traversal_defense() -> None:
    with pytest.raises(ValueError, match="escapes sandbox"):
        write_text("../../escaping_file.txt", "bad")

    with pytest.raises(ValueError, match="escapes sandbox"):
        read_text("/etc/passwd")

    with pytest.raises(ValueError, match="escapes sandbox"):
        delete("../../etc/passwd")


def test_sys_readonly_helpers_and_absolute_guard(tmp_path: Path) -> None:
    sample_dir = tmp_path / "sys_probe"
    sample_dir.mkdir()
    sample_file = sample_dir / "temp1_input"
    sample_file.write_text("58000\n", encoding="utf-8")

    assert sys_exists(str(sample_dir))
    assert sys_is_dir(str(sample_dir))
    assert sys_is_file(str(sample_file))
    assert sys_list_dir(str(sample_dir)) == ["temp1_input"]
    assert sys_read_text(str(sample_file)) == "58000\n"
    assert sys_read_bytes(str(sample_file)) == b"58000\n"

    assert not sys_exists("relative/path.txt")
    assert not sys_is_file("relative/path.txt")
    assert not sys_is_dir("relative/path")
    assert sys_list_dir("relative/path") == []
    with pytest.raises(ValueError, match="must be absolute"):
        sys_read_text("relative/path.txt")
    with pytest.raises(ValueError, match="must be absolute"):
        sys_read_bytes("relative/path.txt")
