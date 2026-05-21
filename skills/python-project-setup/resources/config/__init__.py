"""
Config module entry point.
Auto-loads environment variables and exports all configuration utilities.
"""

from .paths import PROJECT_ROOT, find_project_root
from .files import (
    read_text, write_text, read_json, write_json, read_pickle, write_pickle,
    exists, is_file, is_dir, ensure_dir, delete, list_files, get_abs_path,
    get_size, read_from_pos
)
from .dotenv import load_dotenv, set_value, get_value, remove_value
from .settings import Settings
from .logger import setup_logger, shutdown_logger

# Auto-load environment variables on import
load_dotenv()

__all__ = [
    "PROJECT_ROOT",
    "find_project_root",
    "read_text",
    "write_text",
    "read_json",
    "write_json",
    "read_pickle",
    "write_pickle",
    "exists",
    "is_file",
    "is_dir",
    "ensure_dir",
    "delete",
    "list_files",
    "get_abs_path",
    "get_size",
    "read_from_pos",
    "load_dotenv",
    "set_value",
    "get_value",
    "remove_value",
    "Settings",
    "setup_logger",
    "shutdown_logger",
]