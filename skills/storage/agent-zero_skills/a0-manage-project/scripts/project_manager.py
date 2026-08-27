import os
import sys
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Dynamic root resolution for human-skills
_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR
for p in [_CURRENT_DIR, *_CURRENT_DIR.parents]:
    if (p / "helpers" / "tool.py").exists():
        _SKILLS_ROOT = p
        break
    if (p / "skills" / "helpers" / "tool.py").exists():
        _SKILLS_ROOT = p / "skills"
        break
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))

from helpers.tool import Tool, Response


class ProjectManager(Tool):
    """
    Unified Human Skill tool to manage Agent Zero projects.
    Handles lifecycle (create, list, load, update, delete), instructions & rule templating,
    knowledge base management, environment variables, and git repository cloning/status.
    """
    name: str = "project_manager"
    description: str = (
        "Manage Agent Zero projects: create, configure, update, delete, clone git repos, "
        "add rules/instructions from templates, add knowledge files, and set project variables."
    )
    arguments: dict = {
        "action": "Operation to perform: 'create', 'list', 'load', 'update', 'delete', 'add_rules', 'add_knowledge', 'set_variables', 'clone', 'git_status' (REQUIRED)",
        "project_name": "Unique project identifier (e.g. 'finance-bot', 'my-api'). Required for all actions except 'list'.",
        "projects_dir": "Optional custom path to Agent Zero projects directory (defaults to $A0_PROJECTS_DIR, /a0/usr/projects, ~/.agent-zero/usr/projects, or ./usr/projects).",
        "title": "Human-readable project title (used in 'create', 'update', 'clone').",
        "description": "Short project description (used in 'create', 'update', 'clone').",
        "instructions": "Custom system prompt / instructions string (used in 'create', 'update', 'clone').",
        "color": "Hex color code for UI badge (e.g. '#10B981').",
        "memory": "Memory mode: 'own' (isolated vector DB) or 'global' (shared pool). Defaults to 'own'.",
        "rules": "Comma-separated list of template rule filenames for 'add_rules' (e.g. 'python-coding-style.md, common-git-workflow.md').",
        "filename": "Target filename for 'add_knowledge' (e.g. 'api-docs.md').",
        "content": "Text / markdown content for 'add_knowledge'.",
        "variables": "Multiline KEY=VALUE string for 'set_variables' (e.g. 'API_URL=https://api.com\\nDEBUG=true').",
        "git_url": "Remote Git URL for 'clone' action (REQUIRED for 'clone').",
        "git_token": "Optional Git Personal Access Token for private repo cloning."
    }
    instruction: str = (
        "Use this tool to manage Agent Zero project structures, configuration, memory modes, "
        "and inject domain rule templates into .a0proj/."
    )

    def _resolve_projects_base_dir(self) -> Path:
        """Resolve the root projects directory for Agent Zero."""
        # 1. Custom provided path
        custom_dir = self.args.get("projects_dir")
        if custom_dir:
            p = Path(custom_dir).resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p

        # 2. Environment variable
        env_dir = os.environ.get("A0_PROJECTS_DIR") or os.environ.get("AGENT_ZERO_PROJECTS_DIR")
        if env_dir:
            p = Path(env_dir).resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p

        # 3. Standard locations
        candidates = [
            Path("/a0/usr/projects"),
            Path.home() / ".agent-zero" / "usr" / "projects",
            Path.cwd() / "usr" / "projects",
            Path.cwd() / "projects",
            Path.cwd() / "a0" / "usr" / "projects",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate.resolve()

        # 4. Default fallback to ./usr/projects in current working directory
        default_p = Path.cwd() / "usr" / "projects"
        default_p.mkdir(parents=True, exist_ok=True)
        return default_p.resolve()

    def _get_project_dir(self, name: str) -> Path:
        """Get absolute path to a specific project directory."""
        base_dir = self._resolve_projects_base_dir()
        return base_dir / name

    def _get_meta_dir(self, name: str) -> Path:
        """Get path to .a0proj metadata directory."""
        return self._get_project_dir(name) / ".a0proj"

    def _get_templates_dir(self) -> Path:
        """Locate template files bundled with this skill."""
        return _CURRENT_DIR.parent / "templates"

    def _read_project_json(self, name: str) -> Dict[str, Any]:
        """Read .a0proj/project.json or return defaults."""
        meta_file = self._get_meta_dir(name) / "project.json"
        if meta_file.exists():
            try:
                return json.loads(meta_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "title": name,
            "description": "",
            "instructions": "",
            "color": "#3B82F6",
            "memory": "own",
            "created_at": datetime.now().isoformat()
        }

    def _write_project_json(self, name: str, data: Dict[str, Any]) -> None:
        """Write .a0proj/project.json."""
        meta_dir = self._get_meta_dir(name)
        meta_dir.mkdir(parents=True, exist_ok=True)
        meta_file = meta_dir / "project.json"
        meta_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    async def execute(self, **kwargs) -> Response:
        action = str(self.args.get("action", "")).strip().lower()
        name = str(self.args.get("project_name") or self.args.get("name") or "").strip()

        if not action:
            return Response(message="❌ Error: 'action' argument is required.", break_loop=False)

        try:
            # ── 1. LIST PROJECTS ───────────────────────────────────────────────
            if action == "list":
                base_dir = self._resolve_projects_base_dir()
                project_dirs = [d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith(".")] if base_dir.exists() else []

                projects_data = []
                for p_dir in sorted(project_dirs, key=lambda x: x.name):
                    meta = self._read_project_json(p_dir.name)
                    has_git = (p_dir / ".git").exists()
                    rules_count = len(list((p_dir / ".a0proj" / "instructions").glob("*.md"))) if (p_dir / ".a0proj" / "instructions").exists() else 0
                    knowledge_count = len(list((p_dir / ".a0proj" / "knowledge" / "main").glob("*"))) if (p_dir / ".a0proj" / "knowledge" / "main").exists() else 0
                    
                    projects_data.append({
                        "name": p_dir.name,
                        "title": meta.get("title", p_dir.name),
                        "description": meta.get("description", ""),
                        "color": meta.get("color", "#3B82F6"),
                        "memory": meta.get("memory", "own"),
                        "has_git": has_git,
                        "rules_count": rules_count,
                        "knowledge_count": knowledge_count,
                        "path": str(p_dir)
                    })

                if not projects_data:
                    return Response(
                        message=f"📂 No Agent Zero projects found in `{base_dir}`.\n💡 Use action='create' or action='clone' to initialize a project.",
                        break_loop=False,
                        additional={"data": []}
                    )

                lines = [
                    f"📂 **Agent Zero Projects** ({len(projects_data)} found in `{base_dir}`):\n"
                ]
                for p in projects_data:
                    git_badge = " [Git]" if p["has_git"] else ""
                    lines.append(
                        f"• **{p['name']}**{git_badge} — *{p['title']}*\n"
                        f"  - Description: {p['description'] or '(no description)'}\n"
                        f"  - Memory: `{p['memory']}` | Rules: {p['rules_count']} | Knowledge: {p['knowledge_count']}\n"
                        f"  - Path: `{p['path']}`"
                    )

                return Response(
                    message="\n".join(lines),
                    break_loop=False,
                    additional={"data": projects_data}
                )

            # All subsequent actions require project_name
            if not name:
                return Response(
                    message="❌ Error: 'project_name' is required for this action.",
                    break_loop=False
                )

            # ── 2. CREATE PROJECT ──────────────────────────────────────────────
            if action == "create":
                p_dir = self._get_project_dir(name)
                if p_dir.exists():
                    return Response(
                        message=f"⚠️ Project '{name}' already exists at `{p_dir}`. Use action='update' to modify.",
                        break_loop=False
                    )

                # Create directories
                p_dir.mkdir(parents=True, exist_ok=True)
                meta_dir = p_dir / ".a0proj"
                (meta_dir / "instructions").mkdir(parents=True, exist_ok=True)
                (meta_dir / "knowledge" / "main").mkdir(parents=True, exist_ok=True)

                data = {
                    "title": self.args.get("title") or name.replace("-", " ").replace("_", " ").title(),
                    "description": self.args.get("description", ""),
                    "instructions": self.args.get("instructions", ""),
                    "color": self.args.get("color", "#10B981"),
                    "memory": self.args.get("memory", "own"),
                    "created_at": datetime.now().isoformat()
                }
                self._write_project_json(name, data)

                # Initialize empty variables.env & secrets.env
                (meta_dir / "variables.env").touch(exist_ok=True)
                (meta_dir / "secrets.env").touch(exist_ok=True)

                return Response(
                    message=(
                        f"✅ **Project '{name}' created successfully!**\n\n"
                        f"   📁 Path: `{p_dir}`\n"
                        f"   🏷️ Title: {data['title']}\n"
                        f"   🧠 Memory Mode: `{data['memory']}`\n"
                        f"   ⚙️ Config: `{meta_dir / 'project.json'}`\n\n"
                        f"💡 Next step: Use action='add_rules' to inject coding standards or action='set_variables' for env vars."
                    ),
                    break_loop=False,
                    additional={"data": data}
                )

            # ── 3. LOAD PROJECT ────────────────────────────────────────────────
            elif action == "load":
                p_dir = self._get_project_dir(name)
                if not p_dir.exists():
                    return Response(message=f"❌ Project '{name}' not found at `{p_dir}`.", break_loop=False)

                meta = self._read_project_json(name)
                meta_dir = p_dir / ".a0proj"
                
                rules = [f.name for f in (meta_dir / "instructions").glob("*.md")] if (meta_dir / "instructions").exists() else []
                knowledge = [f.name for f in (meta_dir / "knowledge" / "main").glob("*")] if (meta_dir / "knowledge" / "main").exists() else []
                
                variables_content = ""
                var_file = meta_dir / "variables.env"
                if var_file.exists():
                    variables_content = var_file.read_text(encoding="utf-8")

                output_data = {
                    "name": name,
                    "path": str(p_dir),
                    "metadata": meta,
                    "rules": rules,
                    "knowledge": knowledge,
                    "variables": variables_content,
                    "has_git": (p_dir / ".git").exists()
                }

                report = (
                    f"📋 **Project Configuration: '{name}'**\n\n"
                    f"   📁 Path: `{p_dir}`\n"
                    f"   🏷️ Title: {meta.get('title', name)}\n"
                    f"   📝 Description: {meta.get('description') or '(none)'}\n"
                    f"   🎨 Color: `{meta.get('color', '#3B82F6')}` | Memory: `{meta.get('memory', 'own')}`\n"
                    f"   📜 Injected Rules ({len(rules)}): {', '.join(rules) if rules else '(none)'}\n"
                    f"   📚 Knowledge Files ({len(knowledge)}): {', '.join(knowledge) if knowledge else '(none)'}\n"
                    f"   🔑 Variables Set: {'Yes' if variables_content.strip() else 'None'}\n"
                )
                return Response(message=report, break_loop=False, additional={"data": output_data})

            # ── 4. UPDATE PROJECT ──────────────────────────────────────────────
            elif action == "update":
                p_dir = self._get_project_dir(name)
                if not p_dir.exists():
                    return Response(message=f"❌ Project '{name}' does not exist at `{p_dir}`.", break_loop=False)

                current = self._read_project_json(name)
                if "title" in self.args: current["title"] = self.args["title"]
                if "description" in self.args: current["description"] = self.args["description"]
                if "instructions" in self.args: current["instructions"] = self.args["instructions"]
                if "color" in self.args: current["color"] = self.args["color"]
                if "memory" in self.args: current["memory"] = self.args["memory"]
                current["updated_at"] = datetime.now().isoformat()

                self._write_project_json(name, current)
                return Response(
                    message=f"✅ Project '{name}' configuration updated successfully.",
                    break_loop=False,
                    additional={"data": current}
                )

            # ── 5. DELETE PROJECT ──────────────────────────────────────────────
            elif action == "delete":
                p_dir = self._get_project_dir(name)
                if not p_dir.exists():
                    return Response(message=f"❌ Project '{name}' does not exist at `{p_dir}`.", break_loop=False)

                shutil.rmtree(p_dir)
                return Response(
                    message=f"🗑️ Project '{name}' and its .a0proj metadata deleted successfully from `{p_dir}`.",
                    break_loop=False
                )

            # ── 6. SET VARIABLES ───────────────────────────────────────────────
            elif action == "set_variables":
                p_dir = self._get_project_dir(name)
                meta_dir = p_dir / ".a0proj"
                meta_dir.mkdir(parents=True, exist_ok=True)

                variables_str = self.args.get("variables", "")
                var_file = meta_dir / "variables.env"
                var_file.write_text(variables_str.strip() + "\n", encoding="utf-8")

                return Response(
                    message=f"✅ Variables updated for project '{name}' in `{var_file}`.",
                    break_loop=False
                )

            # ── 7. ADD RULES (TEMPLATES) ───────────────────────────────────────
            elif action == "add_rules":
                rules_list_str = self.args.get("rules", "")
                if not rules_list_str:
                    templates_dir = self._get_templates_dir()
                    available_templates = [f.name for f in templates_dir.glob("*.md")] if templates_dir.exists() else []
                    return Response(
                        message=(
                            f"❌ Error: 'rules' argument is required (comma-separated filenames).\n"
                            f"💡 Available Templates in skill:\n" + "\n".join(f"  • {t}" for t in sorted(available_templates))
                        ),
                        break_loop=False
                    )

                p_dir = self._get_project_dir(name)
                target_instructions_dir = p_dir / ".a0proj" / "instructions"
                target_instructions_dir.mkdir(parents=True, exist_ok=True)

                templates_dir = self._get_templates_dir()
                added_files: List[str] = []
                missing_files: List[str] = []

                for rule_file in [r.strip() for r in rules_list_str.split(",") if r.strip()]:
                    src_file = templates_dir / rule_file
                    if src_file.exists():
                        shutil.copy2(src_file, target_instructions_dir / rule_file)
                        added_files.append(rule_file)
                    else:
                        missing_files.append(rule_file)

                msg_parts = [f"✅ Added {len(added_files)} rule template(s) to `{name}/.a0proj/instructions/`:"]
                for f in added_files:
                    msg_parts.append(f"   • {f}")

                if missing_files:
                    msg_parts.append(f"\n⚠️ Template(s) not found in `{templates_dir}`: {', '.join(missing_files)}")

                return Response(message="\n".join(msg_parts), break_loop=False)

            # ── 8. ADD KNOWLEDGE ───────────────────────────────────────────────
            elif action == "add_knowledge":
                filename = self.args.get("filename")
                content = self.args.get("content")

                if not filename or content is None:
                    return Response(
                        message="❌ Error: Both 'filename' and 'content' arguments are required for 'add_knowledge'.",
                        break_loop=False
                    )

                p_dir = self._get_project_dir(name)
                knowledge_dir = p_dir / ".a0proj" / "knowledge" / "main"
                knowledge_dir.mkdir(parents=True, exist_ok=True)

                target_file = knowledge_dir / filename
                target_file.write_text(content, encoding="utf-8")

                return Response(
                    message=f"✅ Knowledge file '{filename}' ({len(content.encode('utf-8'))} bytes) written to `{target_file}`.",
                    break_loop=False
                )

            # ── 9. CLONE GIT REPOSITORY ────────────────────────────────────────
            elif action == "clone":
                git_url = self.args.get("git_url")
                if not git_url:
                    return Response(message="❌ Error: 'git_url' is required for clone action.", break_loop=False)

                p_dir = self._get_project_dir(name)
                if p_dir.exists() and any(p_dir.iterdir()):
                    return Response(
                        message=f"❌ Cannot clone: Target directory `{p_dir}` already exists and is not empty.",
                        break_loop=False
                    )

                p_dir.parent.mkdir(parents=True, exist_ok=True)

                # Clone command
                clone_cmd = ["git", "clone", git_url, str(p_dir)]
                git_token = self.args.get("git_token")
                if git_token and git_url.startswith("https://"):
                    auth_url = git_url.replace("https://", f"https://x-access-token:{git_token}@")
                    clone_cmd = ["git", "clone", auth_url, str(p_dir)]

                res = subprocess.run(clone_cmd, capture_output=True, text=True)
                if res.returncode != 0:
                    return Response(
                        message=f"❌ Git clone failed:\n{res.stderr}",
                        break_loop=False
                    )

                # Setup .a0proj metadata
                meta_dir = p_dir / ".a0proj"
                (meta_dir / "instructions").mkdir(parents=True, exist_ok=True)
                (meta_dir / "knowledge" / "main").mkdir(parents=True, exist_ok=True)

                data = {
                    "title": self.args.get("title") or name.replace("-", " ").replace("_", " ").title(),
                    "description": self.args.get("description", f"Cloned from {git_url}"),
                    "instructions": self.args.get("instructions", ""),
                    "color": self.args.get("color", "#6366F1"),
                    "memory": self.args.get("memory", "own"),
                    "git_url": git_url,
                    "created_at": datetime.now().isoformat()
                }
                self._write_project_json(name, data)

                return Response(
                    message=(
                        f"✅ **Repository cloned successfully as Agent Zero project '{name}'!**\n\n"
                        f"   📁 Path: `{p_dir}`\n"
                        f"   🌐 Remote: `{git_url}`\n"
                        f"   ⚙️ Metadata initialized in `.a0proj/`"
                    ),
                    break_loop=False,
                    additional={"data": data}
                )

            # ── 10. GIT STATUS ─────────────────────────────────────────────────
            elif action == "git_status":
                p_dir = self._get_project_dir(name)
                if not p_dir.exists():
                    return Response(message=f"❌ Project '{name}' does not exist at `{p_dir}`.", break_loop=False)

                if not (p_dir / ".git").exists():
                    return Response(message=f"ℹ️ Project '{name}' is not a Git repository (no `.git` directory).", break_loop=False)

                status_res = subprocess.run(["git", "status", "--short"], cwd=str(p_dir), capture_output=True, text=True)
                branch_res = subprocess.run(["git", "branch", "--show-current"], cwd=str(p_dir), capture_output=True, text=True)
                log_res = subprocess.run(["git", "log", "-1", "--oneline"], cwd=str(p_dir), capture_output=True, text=True)

                branch = branch_res.stdout.strip() or "HEAD (detached)"
                last_commit = log_res.stdout.strip() or "(no commits)"
                changes = status_res.stdout.strip() or "Clean (no changes)"

                report = (
                    f"🌿 **Git Status for '{name}'** (`{p_dir}`):\n"
                    f"   • Branch: `{branch}`\n"
                    f"   • Latest Commit: `{last_commit}`\n"
                    f"   • Working Tree Status:\n"
                    f"```text\n{changes}\n```"
                )
                return Response(message=report, break_loop=False)

            else:
                return Response(
                    message=f"❌ Error: Unknown action '{action}'.\n💡 Supported actions: 'list', 'create', 'load', 'update', 'delete', 'add_rules', 'add_knowledge', 'set_variables', 'clone', 'git_status'.",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"❌ Error in project_manager tool: {str(e)}",
                break_loop=False
            )
