import subprocess
from pathlib import Path
from helpers.tool import Tool, Response

class Bootstrap(Tool):
    """
    Bootstraps a complete Python project skeleton.
    It executes the resources/bootstrap.py script in the target destination.
    """
    name: str = "bootstrap"
    description: str = "Bootstraps a complete Python project skeleton (directories, gitignore, env, configs, helpers) into an empty directory."
    arguments: dict = {
        "destination": "Target empty directory where the project should be bootstrapped (e.g. '/path/to/new_project')."
    }
    instruction: str = "Use this tool to initialize a brand new Python project."

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(message="❌ Error: 'destination' argument is required.", break_loop=False)

        dest_path = Path(dest_str).resolve()
        
        # Ensure destination exists
        dest_path.mkdir(parents=True, exist_ok=True)

        resource_script = Path(__file__).resolve().parent.parent / "resources" / "initialize" / "bootstrap.py"
        if not resource_script.exists():
            return Response(message=f"❌ Error: bootstrap script not found at {resource_script}", break_loop=False)

        try:
            # Run the bootstrap script inside the destination directory
            result = subprocess.run(
                ["python3", str(resource_script)],
                cwd=str(dest_path),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return Response(message=f"✅ Bootstrap successful in {dest_path}\n\nOutput:\n{result.stdout}", break_loop=False)
            else:
                return Response(message=f"❌ Bootstrap failed with exit code {result.returncode}\n\nError Output:\n{result.stderr}\n\nStandard Output:\n{result.stdout}", break_loop=False)
                
        except Exception as e:
            return Response(message=f"❌ Error running bootstrap: {str(e)}", break_loop=False)
