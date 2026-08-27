import os
import sys
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

if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

from helpers.tool import Tool, Response

try:
    from . import projects, files, git
except ImportError:
    import projects, files, git  # type: ignore


class A0ManageProject(Tool):
    """
    Tool to manage Agent Zero projects.
    
    Actions:
    - create: Create new project
    - list: List all projects
    - load: Load project config
    - delete: Delete project
    - update: Update project settings
    - set_variables: Set environment variables
    - add_rules: Add pre-defined rule files from templates
    - add_knowledge: Add knowledge file
    - clone: Clone git repo as project
    - git_status: Get git status
    """
    name: str = "a0_manage_project"
    description: str = (
        "Manage Agent Zero projects: create, configure, update, delete, clone git repos, "
        "add rules/instructions from templates, add knowledge files, and set project variables."
    )
    arguments: dict = {
        "action": "Operation to perform: 'create', 'list', 'load', 'update', 'delete', 'add_rules', 'add_knowledge', 'set_variables', 'clone', 'git_status' (REQUIRED)",
        "project_name": "Unique project identifier (e.g. 'finance-bot', 'my-api'). Required for all actions except 'list'.",
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

    async def execute(self, **kwargs) -> Response:
        action = str(self.args.get("action", "")).strip().lower()
        # Support both 'project_name' (preferred) and 'name' (legacy/user-habit)
        name = str(self.args.get("project_name") or self.args.get("name") or "").strip()

        if not action:
            return Response(message="Error: 'action' is required", break_loop=False)

        try:
            # ── 1. LIFECYCLE: LIST ─────────────────────────────────────────────
            if action == "list":
                data = projects.get_active_projects_list()
                lines = [f"📂 **Agent Zero Projects** ({len(data)} found):\n"]
                for p in data:
                    lines.append(
                        f"• **{p['name']}** — *{p.get('title', p['name'])}*\n"
                        f"  - Description: {p.get('description') or '(no description)'}\n"
                        f"  - Color: `{p.get('color', '#3B82F6')}`\n"
                        f"  - Path: `{p.get('path', '')}`"
                    )
                return Response(
                    message="\n".join(lines) if data else "📂 No Agent Zero projects found.",
                    break_loop=False,
                    additional={"data": data}
                )

            # All other actions require 'project_name'
            if not name:
                return Response(message="Error: 'project_name' is required for this action", break_loop=False)

            # ── 2. LIFECYCLE: CREATE ───────────────────────────────────────────
            if action == "create":
                data = {
                    "title": self.args.get("title", ""),
                    "description": self.args.get("description", ""),
                    "instructions": self.args.get("instructions", ""),
                    "color": self.args.get("color", "#10B981"),
                    "memory": self.args.get("memory", "own"),
                }
                project_name = projects.create_project(name, data)  # type: ignore
                return Response(
                    message=f"✅ Project '{project_name}' created successfully in `{projects.get_project_folder(project_name)}`",
                    break_loop=False
                )

            # ── 3. LIFECYCLE: LOAD ─────────────────────────────────────────────
            elif action == "load":
                data = projects.load_edit_project_data(name)
                report = (
                    f"📋 **Project Configuration: '{name}'**\n\n"
                    f"   📁 Path: `{projects.get_project_folder(name)}`\n"
                    f"   🏷️ Title: {data.get('title', name)}\n"
                    f"   📝 Description: {data.get('description') or '(none)'}\n"
                    f"   🎨 Color: `{data.get('color', '#3B82F6')}`\n"
                    f"   📜 Instruction Files: {data.get('instruction_files_count', 0)}\n"
                    f"   📚 Knowledge Files: {data.get('knowledge_files_count', 0)}\n"
                    f"   🌿 Git Repo: {'Yes' if data.get('git_status', {}).get('is_git_repo') else 'No'}\n"
                )
                return Response(
                    message=report,
                    break_loop=False,
                    additional={"data": data}
                )

            # ── 4. LIFECYCLE: DELETE ───────────────────────────────────────────
            elif action == "delete":
                deleted_name = projects.delete_project(name)
                return Response(
                    message=f"🗑️ Project '{deleted_name}' deleted successfully",
                    break_loop=False
                )

            # ── 5. CONFIG: UPDATE ──────────────────────────────────────────────
            elif action == "update":
                current = projects.load_edit_project_data(name)
                
                # Update provided fields
                if "title" in self.args: current["title"] = self.args["title"]
                if "description" in self.args: current["description"] = self.args["description"]
                if "instructions" in self.args: current["instructions"] = self.args["instructions"]
                if "color" in self.args: current["color"] = self.args["color"]
                if "memory" in self.args: current["memory"] = self.args["memory"]
                
                projects.update_project(name, current)
                return Response(
                    message=f"✅ Project '{name}' updated successfully",
                    break_loop=False
                )

            # ── 6. CONFIG: SET VARIABLES ───────────────────────────────────────
            elif action == "set_variables":
                variables = self.args.get("variables", "")
                projects.save_project_variables(name, variables)
                return Response(
                    message=f"✅ Variables updated for '{name}'",
                    break_loop=False
                )

            # ── 7. CONTENT: ADD RULES (TEMPLATES) ──────────────────────────────
            elif action == "add_rules":
                rules_list = self.args.get("rules", "")
                if not rules_list:
                    return Response(message="Error: 'rules' argument required (comma-separated filenames)", break_loop=False)
                
                # Base paths
                template_dir = str(_CURRENT_DIR.parent / "templates")
                target_dir = projects.get_project_meta_folder(name, "instructions")
                
                added_files = []
                missing_files = []
                
                # Process each requested rule file
                for rule_file in [r.strip() for r in rules_list.split(",") if r.strip()]:
                    src_path = os.path.join(template_dir, rule_file)
                    
                    if os.path.exists(src_path):
                        content = files.read_file(src_path)
                        dest_path = os.path.join(target_dir, rule_file)
                        files.write_file(dest_path, content)
                        added_files.append(rule_file)
                    else:
                        missing_files.append(rule_file)
                
                msg = f"✅ Added rules to '{name}': {', '.join(added_files)}"
                if missing_files:
                    msg += f"\n⚠️ Warning: Templates not found for: {', '.join(missing_files)}"
                    
                return Response(
                    message=msg,
                    break_loop=False
                )

            # ── 8. CONTENT: ADD KNOWLEDGE ──────────────────────────────────────
            elif action == "add_knowledge":
                filename = self.args.get("filename")
                content = self.args.get("content")
                if not filename or content is None:
                    return Response(message="Error: 'filename' and 'content' required", break_loop=False)
                
                # Ensure it goes to knowledge/main folder
                path = files.get_abs_path(
                    projects.get_project_meta_folder(name, "knowledge", "main"), 
                    filename
                )
                files.write_file(path, content)
                return Response(
                    message=f"✅ Knowledge file '{filename}' added to '{name}' at `{path}`",
                    break_loop=False
                )

            # ── 9. GIT: CLONE ──────────────────────────────────────────────────
            elif action == "clone":
                git_url = self.args.get("git_url")
                if not git_url:
                    return Response(message="Error: 'git_url' required", break_loop=False)
                
                data = {
                    "title": self.args.get("title", ""),
                    "description": self.args.get("description", ""),
                    "instructions": self.args.get("instructions", ""),
                    "color": self.args.get("color", "#6366F1"),
                }
                
                actual_name = projects.clone_git_project(name, git_url, self.args.get("git_token", ""), data)  # type: ignore
                return Response(
                    message=f"✅ Project '{actual_name}' cloned successfully from {git_url}",
                    break_loop=False
                )

            # ── 10. GIT: STATUS ────────────────────────────────────────────────
            elif action == "git_status":
                project_path = projects.get_project_folder(name)
                status = git.get_repo_status(project_path)
                return Response(
                    message=(
                        f"🌿 **Git Status for '{name}'**:\n"
                        f"   • Is Git Repo: {status.get('is_git_repo')}\n"
                        f"   • Branch: `{status.get('current_branch', 'N/A')}`\n"
                        f"   • Dirty: {status.get('is_dirty', False)}\n"
                        f"   • Untracked Files: {status.get('untracked_count', 0)}\n"
                        f"   • Remote URL: `{status.get('remote_url', 'None')}`"
                    ),
                    break_loop=False,
                    additional={"data": status}
                )

            else:
                return Response(
                    message=f"Error: Unknown action '{action}'",
                    break_loop=False
                )

        except Exception as e:
            return Response(
                message=f"Error executing project_manager: {str(e)}",
                break_loop=False
            )
