import subprocess
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
    """
    name: str = "setui"
    description: str = (
        "Scaffolds a complete Next.js + shadcn/ui frontend (web/) with 9 themes, "
        "layout components, secure API client, and OAuth auth pages into the target project."
    )
    arguments: dict = {
        "destination": "Project root where 'web/' directory should be created (e.g. '/path/to/project').",
    }
    instruction: str = (
        "Use this tool to set up a modern frontend layer for any Python/FastAPI project. "
        "Requires Node.js and npm to be installed."
    )

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(
                message="❌ Error: 'destination' argument is required.",
                break_loop=False,
            )

        dest_path = Path(dest_str).resolve()

        # Ensure destination exists
        dest_path.mkdir(parents=True, exist_ok=True)

        resource_script = (
            Path(__file__).resolve().parent.parent / "resources" / "ui" / "setup.py"
        )
        if not resource_script.exists():
            return Response(
                message=f"❌ Error: setup script not found at {resource_script}",
                break_loop=False,
            )

        try:
            result = subprocess.run(
                ["python3", str(resource_script)],
                cwd=str(dest_path),
                capture_output=True,
                text=True,
                timeout=600,  # 10 min timeout for npm installs
            )

            if result.returncode == 0:
                return Response(
                    message=(
                        f"✅ SetUI successful in {dest_path}\n\n"
                        f"Output:\n{result.stdout}"
                    ),
                    break_loop=False,
                )
            else:
                return Response(
                    message=(
                        f"❌ SetUI failed with exit code {result.returncode}\n\n"
                        f"Error Output:\n{result.stderr}\n\n"
                        f"Standard Output:\n{result.stdout}"
                    ),
                    break_loop=False,
                )

        except subprocess.TimeoutExpired:
            return Response(
                message="❌ SetUI timed out after 10 minutes. Check npm/network connectivity.",
                break_loop=False,
            )
        except Exception as e:
            return Response(
                message=f"❌ Error running SetUI: {str(e)}",
                break_loop=False,
            )
