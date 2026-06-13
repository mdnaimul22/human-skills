import json
import os
import subprocess
import sys
from pathlib import Path
from helpers.tool import Tool, Response

class SetUI(Tool):
    """
    Scaffolds a complete Next.js + shadcn/ui + Tailwind CSS frontend
    with 9 themes, layout components, and OAuth auth pages.

    Creates a 'web/' directory in the target project with:
    - Next.js 15 (App Router) + TypeScript
    - shadcn/ui components (30+ pre-installed)
    - 9 unified themes (7 dark + 2 light)
    - Layout shell (Sidebar, Navbar, PageHeader)
    - Auth pages (Login with OAuth buttons)
    - Secure FastAPI API client
    - OpenAPI → TypeScript auto-gen script

    When 'design_query' is provided, bridges with ui-ux-pro-max to generate
    an AI-powered custom theme (colors, fonts) injected into the scaffold.
    """
    name: str = "setui"
    description: str = (
        "Scaffolds a complete Next.js + shadcn/ui frontend (web/) with 9 themes, "
        "layout components, secure API client, and OAuth auth pages into the target project. "
        "Optionally accepts a 'design_query' to generate an AI-powered custom theme via ui-ux-pro-max."
    )
    arguments: dict = {
        "destination": "Project root where 'web/' directory should be created (e.g. '/path/to/project').",
        "design_query": "(Optional) Product/industry description for AI design system generation. "
                        "Example: 'beauty spa wellness', 'fintech crypto dashboard', 'SaaS analytics'. "
                        "When provided, generates a custom theme with industry-matched colors and fonts.",
    }
    instruction: str = (
        "Use this tool to set up a modern frontend layer for any Python/FastAPI project. "
        "Requires Node.js and npm to be installed. "
        "Pass 'design_query' to auto-generate a custom theme matched to your industry/product."
    )

    def _generate_design_system(self, query: str) -> dict | None:
        """Call ui-ux-pro-max's DesignSystemGenerator to get a design system dict."""
        # Locate ui-ux-pro-max scripts directory (sibling skill)
        skills_root = Path(__file__).resolve().parent.parent.parent
        uiux_scripts = skills_root / "ui-ux-pro-max" / "scripts"

        if not uiux_scripts.exists():
            return None

        # Add to sys.path so we can import
        scripts_str = str(uiux_scripts)
        if scripts_str not in sys.path:
            sys.path.insert(0, scripts_str)

        try:
            from design_system import DesignSystemGenerator
            generator = DesignSystemGenerator()
            return generator.generate(query)
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

        resource_script = (
            Path(__file__).resolve().parent.parent / "resources" / "setup.py"
        )
        if not resource_script.exists():
            return Response(
                message=f"❌ Error: setup script not found at {resource_script}",
                break_loop=False,
            )

        # Build environment — pass design system as JSON if query provided
        env = os.environ.copy()
        design_query = self.args.get("design_query", "")
        ds_info = ""

        if design_query:
            design_system = self._generate_design_system(design_query)
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
