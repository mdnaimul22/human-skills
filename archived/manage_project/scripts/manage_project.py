import os
import sys
from pathlib import Path
from tool import Tool, Response
from helpers import projects, files, git

_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR.parents[1]
_HELPERS_DIR = _SKILLS_ROOT / "helpers"

if str(_HELPERS_DIR) not in sys.path:
    sys.path.append(str(_HELPERS_DIR))

if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))



class ManageProject(Tool):
    name = "manage_project"
    description = "Comprehensive tool for lifecycle and configuration management of AI projects."
    arguments = {
        "action": "One of: list, create, load, delete, update, set_variables, add_rules, add_knowledge, clone, git_status",
        "project_name": "Target project identifier.",
        "title": "Project title (create/update/clone).",
        "description": "Project description (create/update/clone).",
        "git_url": "Remote repository URL (clone).",
        "rules": "Comma-separated template filenames (add_rules)."
    }
    instruction = "For Skill instruction run human-skills --skill_info manage_project"

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action")
        # Support both 'project_name' (preferred) and 'name' (legacy/user-habit)
        name = self.args.get("project_name") or self.args.get("name")
        
        if not action:
            return Response(message="Error: 'action' is required", break_loop=False)
            
        try:
            # Lifecycle Actions
            if action == "list":
                data = projects.get_active_projects_list()
                return Response(
                    message=f"Found {len(data)} projects",
                    break_loop=False,
                    additional={"data": data}
                )
                
            # All other actions require 'project_name'
            if not name:
                return Response(message="Error: 'project_name' is required for this action", break_loop=False)

            if action == "create":
                # Prepare basic data
                data = {
                    "title": self.args.get("title", ""),
                    "description": self.args.get("description", ""),
                    "instructions": self.args.get("instructions", ""),
                    "color": self.args.get("color", ""),
                    "memory": self.args.get("memory", "own"),
                }
                project_name = projects.create_project(name, data)
                return Response(
                    message=f"Project '{project_name}' created successfully",
                    break_loop=False
                )

            elif action == "load":
                data = projects.load_edit_project_data(name)
                return Response(
                    message=f"Project '{name}' loaded",
                    break_loop=False,
                    additional={"data": data}
                )

            elif action == "delete":
                projects.delete_project(name)
                return Response(
                    message=f"Project '{name}' deleted",
                    break_loop=False
                )

            # Configuration Actions
            elif action == "update":
                # Get existing data to merge
                current = projects.load_edit_project_data(name)
                
                # Update provided fields
                if "title" in self.args: current["title"] = self.args["title"]
                if "description" in self.args: current["description"] = self.args["description"]
                if "instructions" in self.args: current["instructions"] = self.args["instructions"]
                if "color" in self.args: current["color"] = self.args["color"]
                if "memory" in self.args: current["memory"] = self.args["memory"]
                
                projects.update_project(name, current)
                return Response(
                    message=f"Project '{name}' updated",
                    break_loop=False
                )

            elif action == "set_variables":
                variables = self.args.get("variables", "")
                projects.save_project_variables(name, variables)
                return Response(
                    message=f"Variables updated for '{name}'",
                    break_loop=False
                )

            # Knowledge & Instructions
            elif action == "add_rules":
                rules_list = self.args.get("rules", "")
                if not rules_list:
                    return Response(message="Error: 'rules' argument required (comma-separated filenames)", break_loop=False)
                
                # Base paths
                template_dir = files.get_abs_path("usr/skills/project-setup/templates")
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
                
                msg = f"Added rules: {', '.join(added_files)}"
                if missing_files:
                    msg += f". Warning: Templates not found for: {', '.join(missing_files)}"
                    
                return Response(
                    message=msg,
                    break_loop=False
                )

            elif action == "add_knowledge":
                filename = self.args.get("filename")
                content = self.args.get("content")
                if not filename or not content:
                    return Response(message="Error: 'filename' and 'content' required", break_loop=False)
                
                # Ensure it goes to knowledge/main folder
                path = files.get_abs_path(
                    projects.get_project_meta_folder(name, "knowledge", "main"), 
                    filename
                )
                files.write_file(path, content)
                return Response(
                    message=f"Knowledge file '{filename}' added to '{name}'",
                    break_loop=False
                )

            # Git Operations
            elif action == "clone":
                git_url = self.args.get("git_url")
                if not git_url:
                    return Response(message="Error: 'git_url' required", break_loop=False)
                
                data = {
                    "title": self.args.get("title", ""),
                    "description": self.args.get("description", ""),
                    "instructions": self.args.get("instructions", ""),
                    "color": self.args.get("color", ""),
                }
                
                projects.clone_git_project(name, git_url, self.args.get("git_token", ""), data)
                return Response(
                    message=f"Project '{name}' cloned from {git_url}",
                    break_loop=False
                )

            elif action == "git_status":
                project_path = projects.get_project_folder(name)
                status = git.get_repo_status(project_path)
                return Response(
                    message=f"Git status for '{name}' retrieved",
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
