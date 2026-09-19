from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from helpers.tool import Tool, Response

class SetUI(Tool):
    name: str = "setui"
    description: str = (
        "Scaffolds a complete Next.js frontend (web/) or React Chrome Extension (extension/) "
        "with 11 themes, layout components, secure API client, and layout pages. "
        "Optionally accepts a 'design_query' to generate an AI-powered custom theme via ui-ux-pro-max."
    )
    arguments: dict = {
        "destination": "Project root where the client directory should be created (e.g. '/path/to/project').",
        "action": "(Optional) The client template to scaffold: 'frontend' (default, Next.js web client) or 'chrome-extension' (React extension).",
        "design_query": "(Optional) Product/industry description for AI design system generation. "
                        "Example: 'beauty spa wellness', 'fintech crypto dashboard', 'SaaS analytics'. "
                        "When provided, generates a custom theme with industry-matched colors and fonts.",
    }
    instruction: str = (
        "Use this tool to set up a modern frontend layer for any Python/FastAPI project. "
        "Requires Node.js and npm to be installed. "
        "Pass 'design_query' to auto-generate a custom theme matched to your industry/product."
    )

    def _generate_design_system(
        self,
        query: str,
        project_name: str | None = None,
        output_dir: str | None = None,
    ) -> dict | None:
        storage_root = Path(__file__).resolve().parents[3]
        target_scripts = (
            storage_root
            / "nextlevelbuilder_ui-ux-pro-max"
            / "ui-ux-pro-max"
            / "scripts"
        )
        if not target_scripts.exists():
            target_scripts = storage_root / "my_skills" / "ui-ux-pro-max" / "scripts"
        if not target_scripts.exists():
            return None

        scripts_str = str(target_scripts)
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)

        try:
            from design_system import DesignSystemGenerator, persist_design_system
            generator = DesignSystemGenerator()
            ds = generator.generate(query, project_name=project_name)
            if output_dir:
                try:
                    persist_design_system(ds, output_dir=output_dir)
                except Exception:
                    pass
            return ds
        except Exception:
            return None
        finally:
            if scripts_str in sys.path:
                sys.path.remove(scripts_str)

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(
                message="❌ Error: 'destination' argument is required.",
                break_loop=False,
            )

        dest_path = Path(dest_str).resolve()
        dest_path.mkdir(parents=True, exist_ok=True)

        action = self.args.get("action", "frontend")
        if action == "chrome-extension":
            script_rel_path = "templates/chrome-extension/setup.py"
        else:
            script_rel_path = "templates/frontend/setup.py"

        resource_script = (
            Path(__file__).resolve().parent.parent / script_rel_path
        )
        if not resource_script.exists():
            return Response(
                message=f"❌ Error: setup script not found at {resource_script} (action: {action})",
                break_loop=False,
            )

        env = os.environ.copy()
        design_query = self.args.get("design_query", "")
        ds_info = ""

        if design_query:
            design_system = self._generate_design_system(
                design_query,
                project_name=dest_path.name,
                output_dir=str(dest_path),
            )
            if design_system:
                env["DESIGN_SYSTEM_JSON"] = json.dumps(design_system, ensure_ascii=False)
                ds_info = f"\n🧠 Design system generated for: \"{design_query}\""
            else:
                ds_info = "\n⚠️ ui-ux-pro-max skill not found. Scaffolding without custom theme."

        try:
            result = subprocess.run(
                ["python3", "-u", str(resource_script)],
                cwd=str(dest_path),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=2400,
            )

            if result.returncode == 0:
                return Response(
                    message=(
                        f"✅ SetUI successful in {dest_path}{ds_info}\n\n"
                        f"Output:\n{result.stdout}"
                    ),
                    break_loop=False,
                )
            else:
                return Response(
                    message=(
                        f"❌ SetUI failed with exit code {result.returncode}\n\n"
                        f"Output:\n{result.stdout}"
                    ),
                    break_loop=False,
                )

        except subprocess.TimeoutExpired as e:
            partial = e.stdout or "" if hasattr(e, "stdout") else ""
            return Response(
                message=(
                    f"❌ SetUI timed out after 40 minutes.\n"
                    f"Partial output:\n{partial[-500:]}\n\n"
                    f"Hint: Check npm/network connectivity."
                ),
                break_loop=False,
            )
        except Exception as e:
            return Response(
                message=f"❌ Error running SetUI: {str(e)}",
                break_loop=False,
            )
