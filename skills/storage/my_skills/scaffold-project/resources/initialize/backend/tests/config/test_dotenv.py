import os
import uuid
import pytest
from src.config.dotenv import (
    load_dotenv,
    set_value,
    get_value,
    remove_value,
    parse_env_dict,
)
from src.config.files import write_text, read_text, delete, exists, ensure_dir


@pytest.fixture
def tmp_env_workspace():
    test_id = f"test_env_{uuid.uuid4().hex[:8]}"
    rel_dir = f"data/test_env_{test_id}"
    ensure_dir(rel_dir)
    rel_env = f"{rel_dir}/.custom_secret_1e2n3v"
    write_text(rel_env, "PORT=9000\nDEBUG=true\n# Comment line\nINVALID_LINE\n")
    yield rel_env, rel_dir
    delete(rel_dir)


def test_parse_env_dict(tmp_env_workspace: tuple[str, str]) -> None:
    rel_env, _ = tmp_env_workspace
    parsed = parse_env_dict(rel_env)
    assert parsed == {"PORT": "9000", "DEBUG": "true"}
    assert parse_env_dict("non_existent_file.env") == {}


def test_load_and_mutate_values(tmp_env_workspace: tuple[str, str]) -> None:
    rel_env, _ = tmp_env_workspace
    load_dotenv(rel_env, override=True)
    assert get_value("PORT") == "9000"
    assert get_value("DEBUG") == "true"

    set_value("NEW_VAR", "injected_val", path=rel_env)
    assert get_value("NEW_VAR") == "injected_val"
    assert "NEW_VAR=injected_val" in read_text(rel_env)

    remove_value("DEBUG", path=rel_env)
    assert get_value("DEBUG") == ""
    assert "DEBUG" not in read_text(rel_env)
    assert "DEBUG" not in os.environ
