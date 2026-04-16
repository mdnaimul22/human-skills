import os
import sys
import shutil
import subprocess
from pathlib import Path
from helpers.tool import Tool, Response

class OpenevolveTool(Tool):
    name = "OpenevolveTool"
    description = "Wrapper tool to manage and execute the OpenEvolve evolutionary coding engine."
    arguments = {
        "action": "One of: install, upgrade"
    }
    instruction = "Executes OpenEvolve initialization and runs."

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action")
        
        if not action:
            return Response(message="Error: 'action' argument is required.", break_loop=False)

        if action == "install":
            try:
                # Install via global pip
                subprocess.run([sys.executable, "-m", "pip", "install", "openevolve"], check=True, capture_output=True)
                
                # Verify
                result = subprocess.run(["openevolve-run", "-h"], capture_output=True, text=True)
                if "usage: openevolve-run [-h] [--config CONFIG] [--output OUTPUT]" in result.stdout:
                    return Response(message="✅ Openevolve installed sccessfully", break_loop=False)
                else:
                    return Response(message="Installation completed, but verification failed.", break_loop=False)
            
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode() if e.stderr else str(e)
                return Response(message=f"Install Error: {err_msg}", break_loop=False)
            except FileNotFoundError:
                return Response(message="Error: openevolve-run command not found after installation.", break_loop=False)

        elif action == "upgrade":
            try:
                # Upgrade via global pip
                subprocess.run([sys.executable, "-m", "pip", "install", "openevolve", "--upgrade"], check=True, capture_output=True)
                
                # Verify
                result = subprocess.run(["openevolve-run", "-h"], capture_output=True, text=True)
                if "usage: openevolve-run [-h] [--config CONFIG] [--output OUTPUT]" in result.stdout:
                    return Response(message="✅ Openevolve আপগ্রেডেড sccessfully", break_loop=False)
                else:
                    return Response(message="Upgrade completed, but verification failed.", break_loop=False)
                    
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode() if e.stderr else str(e)
                return Response(message=f"Upgrade Error: {err_msg}", break_loop=False)
            except FileNotFoundError:
                return Response(message="Error: openevolve-run command not found after upgrade.", break_loop=False)

        elif action == "init":
            target_path = self.args.get("path", os.getcwd())
            project_dir = self.args.get("project_dir", "evolution_project")
            
            target_full_path = Path(target_path) / project_dir
            source_skeleton = Path(__file__).parent.parent / "skeleton"
            
            if not source_skeleton.exists():
                return Response(message=f"Error: Skeleton directory not found at {source_skeleton}", break_loop=False)
                
            try:
                target_full_path.mkdir(parents=True, exist_ok=True)
                for file_name in ["config.yaml", "initial_program.py", "evaluator.py", "test_evaluator.py"]:
                    src_file = source_skeleton / file_name
                    if src_file.exists():
                        shutil.copy2(src_file, target_full_path / file_name)
                        
                msg = (
                    f"✅ Skeleton evolutionary project generated at {target_full_path}\n"
                    "✅ config.yaml\n"
                    "✅ initial_program.py\n"
                    "✅ evaluator.py\n"
                    "✅ test_evaluator.py\n"
                    "Now Configure as your needs"
                )
                return Response(message=msg, break_loop=False)
                
            except Exception as e:
                return Response(message=f"Error creating project structure: {str(e)}", break_loop=False)

        elif action == "run":
            # Example placeholder for running the evolution
            return Response(message="Action 'run' is planned but not fully implemented yet.", break_loop=False)

        elif action == "example":
            # Example placeholder for loading an example
            return Response(message="Action 'example' is planned but not fully implemented yet.", break_loop=False)

        else:
            return Response(message=f"Unknown action: {action}", break_loop=False)
