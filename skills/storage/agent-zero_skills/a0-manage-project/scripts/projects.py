import os
import sys
import json
import re
from typing import NotRequired, TypedDict, TYPE_CHECKING, cast, Any, Dict, List, Optional

try:
    from . import files, git
except ImportError:
    try:
        import files, git
    except ImportError:
        from helpers import files, git  # type: ignore

if TYPE_CHECKING:
    from agent import AgentContext  # type: ignore


PROJECTS_PARENT_DIR = "usr/projects"
PROJECT_META_DIR = ".a0proj"
PROJECT_INSTRUCTIONS_DIR = "instructions"
PROJECT_KNOWLEDGE_DIR = "knowledge"
PROJECT_SKILLS_DIR = "skills"
PROJECT_HEADER_FILE = "project.json"
PROJECT_MCP_SERVERS_FILE = "mcp_servers.json"
PROJECT_AGENTS_MD_FILES = (
    "AGENTS.override.md",
    "AGENTS.Override.md",
    "AGENTS.md",
    "Agents.md",
    "agents.md",
)
DEFAULT_MCP_SERVERS_CONFIG = '{\n    "mcpServers": {}\n}'
CONTEXT_DATA_KEY_PROJECT = "project"


# ── Internal Helpers ───────────────────────────────────────────────────────────

class _DirtyJson:
    """Robust JSON parser handling comments, trailing commas, and formatting."""
    @staticmethod
    def parse(s: str) -> Any:
        if not s or not s.strip():
            return {}
        try:
            return json.loads(s)
        except Exception:
            # Strip JS/C-style comments
            cleaned = re.sub(r"//.*?\n|/\*.*?\*/", "", s, flags=re.S)
            # Strip trailing commas
            cleaned = re.sub(r",\s*([\]}])", r"\1", cleaned)
            return json.loads(cleaned)

    @staticmethod
    def stringify(obj: Any, indent: int = 2) -> str:
        return json.dumps(obj, indent=indent, ensure_ascii=False)


dirty_json = _DirtyJson()


class PrintStyle:
    @staticmethod
    def error(msg: str):
        print(f"[ERROR] {msg}", file=sys.stderr)
    @staticmethod
    def info(msg: str):
        print(f"[INFO] {msg}")


def extensible(func):
    """Pass-through decorator for extensible functions."""
    return func


# ── Data Types ────────────────────────────────────────────────────────────────

class FileStructureInjectionSettings(TypedDict):
    enabled: bool
    max_depth: int
    max_files: int
    max_folders: int
    max_lines: int
    gitignore: str


class SubAgentSettings(TypedDict):
    enabled: bool


class BasicProjectData(TypedDict):
    title: str
    description: str
    instructions: str
    include_agents_md: NotRequired[bool]
    mcp_servers: NotRequired[str]
    color: str
    git_url: str
    file_structure: FileStructureInjectionSettings


class GitStatusData(TypedDict, total=False):
    is_git_repo: bool
    remote_url: str
    current_branch: str
    is_dirty: bool
    untracked_count: int
    last_commit: dict
    error: str


class EditProjectData(BasicProjectData):
    name: str
    instruction_files_count: int
    knowledge_files_count: int
    variables: str
    secrets: str
    mcp_servers: str
    git_status: GitStatusData


ProjectExtendedData = dict[str, object]
_PROJECT_CORE_EDIT_KEYS = frozenset(BasicProjectData.__annotations__) | frozenset(
    EditProjectData.__annotations__
)
_PROJECT_TRANSIENT_INPUT_KEYS = frozenset({"git_token", "subagents"})


# ── Folder & Path Resolution ──────────────────────────────────────────────────

def get_projects_parent_folder() -> str:
    """Resolve projects parent directory (supporting env vars & standard locations)."""
    env_dir = os.environ.get("A0_PROJECTS_DIR") or os.environ.get("AGENT_ZERO_PROJECTS_DIR")
    if env_dir:
        return os.path.abspath(env_dir)

    candidates = [
        "/a0/usr/projects",
        os.path.expanduser("~/.agent-zero/usr/projects"),
        os.path.join(files.get_base_dir(), "usr/projects"),
        os.path.join(files.get_base_dir(), "projects"),
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.isdir(c):
            return os.path.abspath(c)

    return files.get_abs_path(PROJECTS_PARENT_DIR)


def get_project_folder(name: str) -> str:
    return files.get_abs_path(get_projects_parent_folder(), name)


def get_project_meta(name: str, *sub_dirs: str) -> str:
    return files.get_abs_path(get_project_folder(name), PROJECT_META_DIR, *sub_dirs)


def get_project_meta_folder(name: str, *sub_dirs: str) -> str:
    """Get and ensure metadata folder exists."""
    p = get_project_meta(name, *sub_dirs)
    files.create_dir(p)
    return p


def validate_project_name(name: str | None) -> str:
    candidate = str(name or "").strip()
    if (
        not candidate
        or candidate in {".", ".."}
        or os.path.basename(candidate) != candidate
    ):
        raise ValueError("Invalid project name")
    return candidate


# ── Lifecycle Functions ───────────────────────────────────────────────────────

def delete_project(name: str) -> str:
    abs_path = get_project_folder(name)
    files.delete_dir(abs_path)
    try:
        deactivate_project_in_chats(name)
    except Exception:
        pass
    return name


def create_project(name: str, data: BasicProjectData) -> str:
    extended_data = _project_extended_data_for_save(data)
    mcp_servers = data.get("mcp_servers") if isinstance(data, dict) else None
    abs_path = files.create_dir_safe(
        get_project_folder(name), rename_format="{name}_{number}"
    )
    actual_name = files.basename(abs_path)
    create_project_meta_folders(actual_name)
    data = _normalizeBasicData(data)
    save_project_header(actual_name, data)
    save_project_mcp_servers(actual_name, mcp_servers or DEFAULT_MCP_SERVERS_CONFIG)
    save_project_extended_data(actual_name, extended_data)
    return actual_name


def clone_git_project(name: str, git_url: str, git_token: str, data: BasicProjectData) -> str:
    """Clone a git repository as a new A0 project."""
    extended_data = _project_extended_data_for_save(data)
    mcp_servers = data.get("mcp_servers") if isinstance(data, dict) else None
    
    abs_path = files.create_dir_safe(
        get_project_folder(name), rename_format="{name}_{number}"
    )
    actual_name = files.basename(abs_path)
    
    try:
        # Clone with token via http header
        git.clone_repo(git_url, abs_path, token=git_token)
        clean_url = git.strip_auth_from_url(git_url)
        
        # Check if cloned repo already has .a0proj
        meta_path = os.path.join(abs_path, PROJECT_META_DIR, PROJECT_HEADER_FILE)
        if os.path.exists(meta_path):
            cloned_header: BasicProjectData = dirty_json.parse(files.read_file(meta_path)) # type: ignore
            cloned_header["title"] = data.get("title") or cloned_header.get("title", "")
            cloned_header["color"] = data.get("color") or cloned_header.get("color", "")
            cloned_header["git_url"] = clean_url
            save_project_header(actual_name, cloned_header)
        else:
            create_project_meta_folders(actual_name)
            data = _normalizeBasicData(data)
            data["git_url"] = clean_url
            save_project_header(actual_name, data)

        if mcp_servers:
            save_project_mcp_servers(actual_name, mcp_servers)
        save_project_extended_data(actual_name, extended_data)
        
        return actual_name
    except Exception as e:
        try:
            files.delete_dir(abs_path)
        except Exception:
            pass
        raise e


def load_project_header(name: str) -> dict:
    abs_path = get_project_meta(name, PROJECT_HEADER_FILE)
    if not os.path.exists(abs_path):
        return {"name": name, "title": name}
    header: dict = dirty_json.parse(files.read_file(abs_path))
    header["name"] = name
    return header


def _default_file_structure_settings() -> FileStructureInjectionSettings:
    return FileStructureInjectionSettings(
        enabled=True,
        max_depth=5,
        max_files=20,
        max_folders=20,
        max_lines=250,
        gitignore="",
    )


def _normalizeBasicData(data: BasicProjectData) -> BasicProjectData:
    return {
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "instructions": data.get("instructions", ""),
        "include_agents_md": _normalize_include_agents_md(
            data.get("include_agents_md", True)
        ),
        "color": data.get("color", ""),
        "git_url": data.get("git_url", ""),
        "file_structure": data.get(
            "file_structure",
            _default_file_structure_settings(),
        ),
    }


def _normalizeEditData(data: EditProjectData) -> EditProjectData:
    normalized: EditProjectData = {
        "name": data.get("name", ""),
        "title": data.get("title", ""),
        "description": data.get("description", ""),
        "instructions": data.get("instructions", ""),
        "include_agents_md": _normalize_include_agents_md(
            data.get("include_agents_md", True)
        ),
        "variables": data.get("variables", ""),
        "mcp_servers": data.get("mcp_servers", DEFAULT_MCP_SERVERS_CONFIG),
        "color": data.get("color", ""),
        "git_url": data.get("git_url", ""),
        "git_status": data.get("git_status", {"is_git_repo": False}),
        "instruction_files_count": data.get("instruction_files_count", 0),
        "knowledge_files_count": data.get("knowledge_files_count", 0),
        "secrets": data.get("secrets", ""),
        "file_structure": data.get(
            "file_structure",
            _default_file_structure_settings(),
        ),
    }
    return normalized


def _edit_data_to_basic_data(data: EditProjectData) -> BasicProjectData:
    return _normalizeBasicData(data)


def update_project(name: str, data: EditProjectData) -> str:
    extended_data = _project_extended_data_for_save(data)

    current = load_edit_project_data(name)
    current.update(data)
    current = _normalizeEditData(current)

    header = _edit_data_to_basic_data(current)
    save_project_header(name, header)

    save_project_variables(name, current.get("variables", ""))
    save_project_secrets(name, current.get("secrets", ""))
    save_project_mcp_servers(name, current.get("mcp_servers", DEFAULT_MCP_SERVERS_CONFIG))
    save_project_extended_data(name, extended_data)

    try:
        reactivate_project_in_chats(name)
    except Exception:
        pass
    return name


def load_basic_project_data(name: str) -> BasicProjectData:
    data = cast(BasicProjectData, load_project_header(name))
    return _normalizeBasicData(data)


def load_edit_project_data(name: str) -> EditProjectData:
    data = load_basic_project_data(name)
    create_project_meta_folders(name)
    additional_instructions = get_additional_instructions_files(name)
    variables = load_project_variables(name)
    mcp_servers = load_project_mcp_servers(name)
    secrets = load_project_secrets_masked(name)
    knowledge_files_count = get_knowledge_files_count(name)
    git_status = cast(GitStatusData, git.get_repo_status(get_project_folder(name)))
    
    output = cast(
        EditProjectData,
        {
            **data,
            "name": name,
            "instruction_files_count": len(additional_instructions),
            "knowledge_files_count": knowledge_files_count,
            "variables": variables,
            "mcp_servers": mcp_servers,
            "secrets": secrets,
            "git_status": git_status,
        },
    )
    normalized = _normalizeEditData(output)
    _merge_project_extended_data(normalized, load_project_extended_data(name))
    return normalized


def save_project_header(name: str, data: BasicProjectData) -> None:
    header = dirty_json.stringify(_project_header_for_save(data))
    abs_path = get_project_meta(name, PROJECT_HEADER_FILE)
    files.write_file(abs_path, header)


@extensible
def load_project_extended_data(name: str) -> ProjectExtendedData:
    return {}


@extensible
def save_project_extended_data(name: str, project_data: ProjectExtendedData) -> None:
    return None


def _project_extended_data_for_save(data: object) -> ProjectExtendedData:
    if not isinstance(data, dict):
        return {}
    return {
        str(key): value
        for key, value in data.items()
        if str(key) not in _PROJECT_CORE_EDIT_KEYS
        and str(key) not in _PROJECT_TRANSIENT_INPUT_KEYS
    }


def _merge_project_extended_data(
    data: EditProjectData,
    extended_data: object,
) -> None:
    if not isinstance(extended_data, dict):
        return

    conflicts = sorted(str(key) for key in extended_data if key in _PROJECT_CORE_EDIT_KEYS)
    if conflicts:
        raise ValueError(
            "Project extension data cannot overwrite core project fields: "
            + ", ".join(conflicts)
        )

    data.update(extended_data)  # type: ignore[typeddict-item]


def load_project_mcp_servers(name: str) -> str:
    project_name = validate_project_name(name)
    try:
        return files.read_file(get_project_meta(project_name, PROJECT_MCP_SERVERS_FILE))
    except Exception:
        return DEFAULT_MCP_SERVERS_CONFIG


def save_project_mcp_servers(name: str, mcp_servers: str) -> None:
    project_name = validate_project_name(name)
    content = mcp_servers if isinstance(mcp_servers, str) else DEFAULT_MCP_SERVERS_CONFIG
    files.write_file(get_project_meta(project_name, PROJECT_MCP_SERVERS_FILE), content)


def get_active_projects_list() -> List[Dict[str, Any]]:
    parent_dir = get_projects_parent_folder()
    if not os.path.exists(parent_dir):
        return []
    return _get_projects_list(parent_dir)


def _get_projects_list(parent_dir: str) -> List[Dict[str, Any]]:
    projects = []
    if not os.path.exists(parent_dir):
        return projects

    for name in os.listdir(parent_dir):
        try:
            abs_path = os.path.join(parent_dir, name)
            if os.path.isdir(abs_path) and not name.startswith("."):
                project_data = load_basic_project_data(name)
                projects.append(
                    {
                        "name": name,
                        "title": project_data.get("title", name),
                        "description": project_data.get("description", ""),
                        "color": project_data.get("color", "#3B82F6"),
                        "path": abs_path
                    }
                )
        except Exception as e:
            PrintStyle.error(f"Error loading project {name}: {str(e)}")

    projects.sort(key=lambda x: x["name"])
    return projects


# ── Chats & Context Hooks (Agent Zero Runtime Compatibility) ──────────────────

def reactivate_project_in_chats(name: str) -> None:
    try:
        from agent import AgentContext  # type: ignore
        for context in AgentContext.all():
            if context.get_data(CONTEXT_DATA_KEY_PROJECT) == name:
                activate_project(context.id, name, mark_dirty=False)
    except Exception:
        pass


def deactivate_project_in_chats(name: str) -> None:
    try:
        from agent import AgentContext  # type: ignore
        for context in AgentContext.all():
            if context.get_data(CONTEXT_DATA_KEY_PROJECT) == name:
                deactivate_project(context.id, mark_dirty=False)
    except Exception:
        pass


def activate_project(context_id: str, name: str, *, mark_dirty: bool = True) -> None:
    try:
        from agent import AgentContext  # type: ignore
        data = load_edit_project_data(name)
        context = AgentContext.get(context_id)
        if context:
            context.set_data(CONTEXT_DATA_KEY_PROJECT, name)
    except Exception:
        pass


def deactivate_project(context_id: str, *, mark_dirty: bool = True) -> None:
    try:
        from agent import AgentContext  # type: ignore
        context = AgentContext.get(context_id)
        if context:
            context.set_data(CONTEXT_DATA_KEY_PROJECT, None)
    except Exception:
        pass


# ── Instructions, Knowledge & Variables ───────────────────────────────────────

def get_additional_instructions_files(name: str) -> Dict[str, str]:
    instructions_folder = get_project_meta(name, PROJECT_INSTRUCTIONS_DIR)
    return files.read_text_files_in_dir(instructions_folder)


def get_knowledge_files_count(name: str) -> int:
    knowledge_folder = get_project_meta(name, PROJECT_KNOWLEDGE_DIR)
    return len(files.list_files_in_dir_recursively(knowledge_folder))


def load_project_variables(name: str) -> str:
    try:
        abs_path = get_project_meta(name, "variables.env")
        return files.read_file(abs_path)
    except Exception:
        return ""


def save_project_variables(name: str, variables: str) -> None:
    abs_path = get_project_meta(name, "variables.env")
    files.write_file(abs_path, variables)


def load_project_secrets_masked(name: str, merge_with_global: bool = False) -> str:
    try:
        from helpers import secrets  # type: ignore
        mgr = secrets.get_project_secrets_manager(name, merge_with_global)
        return mgr.get_masked_secrets()
    except Exception:
        abs_path = get_project_meta(name, "secrets.env")
        return "***" if os.path.exists(abs_path) else ""


def save_project_secrets(name: str, secrets_str: str) -> None:
    try:
        from helpers.secrets import get_project_secrets_manager  # type: ignore
        secrets_manager = get_project_secrets_manager(name)
        secrets_manager.save_secrets_with_merge(secrets_str)
    except Exception:
        abs_path = get_project_meta(name, "secrets.env")
        files.write_file(abs_path, secrets_str)


def create_project_meta_folders(name: str) -> None:
    files.create_dir(get_project_meta(name, PROJECT_INSTRUCTIONS_DIR))
    files.create_dir(get_project_meta(name, PROJECT_KNOWLEDGE_DIR))
    files.create_dir(get_project_meta(name, PROJECT_KNOWLEDGE_DIR, "main"))
    files.create_dir(get_project_meta(name, PROJECT_SKILLS_DIR))


def _normalize_include_agents_md(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off"}
    return bool(value)


def _project_header_for_save(data: BasicProjectData) -> dict:
    header = dict(data)
    header["include_agents_md"] = _normalize_include_agents_md(
        header.get("include_agents_md", True)
    )
    return header
