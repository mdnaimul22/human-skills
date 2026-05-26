import os
import sys
import shutil
import subprocess
from pathlib import Path
from helpers.tool import Tool, Response

# Setup path convention following tree_gen.py
_CURRENT_DIR = Path(__file__).resolve().parent
_SKILLS_ROOT = _CURRENT_DIR.parent.parent
if str(_SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SKILLS_ROOT))

class OpenevolveTool(Tool):
    """
    Wrapper tool to manage and execute the OpenEvolve evolutionary coding engine.
    Supports installation, project initialization, and running evolutionary searches.
    """
    name = "OpenevolveTool"
    description = "Manage and execute the OpenEvolve evolutionary coding engine for autonomous code optimization."
    arguments = {
        "action": "One of: install, upgrade, init, run, list_example, show_example (REQUIRED)",
        "path": "Target directory for project initialization or execution.",
        "project_dir": "Name of the new directory to create for first 'init'.",
        "max_iterations": "Override maximum evolution iterations for 'run'.",
        "output": "Directory where evolution artifacts and checkpoints will be saved.",
        "checkpoint": "Path to a specific checkpoint to resume evolution from.",
        "example_view": "Name of the example to inspect (used with 'show_example')."
    }
    instruction = "For detailed skill instructions run: human-skills --skill_info openevolve-evolutionary-coding"

    async def execute(self, **kwargs) -> Response:
        action = self.args.get("action")
        
        if not action:
            return Response(message="Error: 'action' argument is required.", break_loop=False)

        # --- ARGUMENT VALIDATION ---
        allowed_args = {
            "install": ["action"],
            "upgrade": ["action"],
            "init": ["action", "path", "project_dir"],
            "run": ["action", "path", "max_iterations", "output", "checkpoint"],
            "list_example": ["action"],
            "show_example": ["action", "example_view"]
        }

        if action in allowed_args:
            valid_keys = allowed_args[action]
            invalid_keys = [k for k in self.args.keys() if k not in valid_keys]
            if invalid_keys:
                msg = f"❌ Error: Invalid argument(s) provided for action '{action}': {', '.join(invalid_keys)}\n"
                msg += f"💡 Available arguments for '{action}': {', '.join(valid_keys)}"
                return Response(message=msg, break_loop=False)

        if action == "install":
            try:
                # Install via global pip
                subprocess.run([sys.executable, "-m", "pip", "install", "openevolve"], check=True, capture_output=True)
                
                # Verify installation
                result = subprocess.run(["openevolve-run", "-h"], capture_output=True, text=True)
                if "usage: openevolve-run [-h] [--config CONFIG] [--output OUTPUT]" in result.stdout:
                    return Response(message="✅ Openevolve installed successfully", break_loop=False)
                else:
                    return Response(message="⚠️ Installation completed, but CLI verification failed.", break_loop=False)
            
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode() if e.stderr else str(e)
                return Response(message=f"❌ Installation Error: {err_msg}", break_loop=False)
            except FileNotFoundError:
                return Response(message="❌ Error: 'openevolve-run' command not found in environment path.", break_loop=False)

        elif action == "upgrade":
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "openevolve", "--upgrade"], check=True, capture_output=True)
                
                # Verify
                result = subprocess.run(["openevolve-run", "-h"], capture_output=True, text=True)
                if "usage: openevolve-run [-h] [--config CONFIG] [--output OUTPUT]" in result.stdout:
                    return Response(message="✅ Openevolve upgraded successfully", break_loop=False)
                else:
                    return Response(message="Upgrade completed, but verification failed.", break_loop=False)
                    
            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.decode() if e.stderr else str(e)
                return Response(message=f"Upgrade Error: {err_msg}", break_loop=False)
            except FileNotFoundError:
                return Response(message="Error: openevolve-run command not found after upgrade.", break_loop=False)

        elif action == "init":
            target_path = self.args.get("path", os.getcwd())
            project_dir = self.args.get("project_dir")
            
            if not project_dir:
                return Response(message="❌ Error: 'project_dir' argument is required but not provided. You MUST specify a new directory name to initialize the project.", break_loop=False)

            target_full_path = Path(target_path) / project_dir
            # Skeleton is located relative to this script
            source_skeleton = Path(__file__).parent.parent / "skeleton"
            
            if not source_skeleton.exists():
                return Response(message=f"❌ Error: Skeleton templates not found at {source_skeleton}", break_loop=False)
                
            if target_full_path.exists():
                existing_core_files = [f.name for f in target_full_path.iterdir() if f.is_file() and f.name in ["config.yaml", "initial_program.py", "evaluator.py"]]
                if existing_core_files:
                    return Response(message=f"❌ Error: Project already initialized at '{target_full_path}'. Please analyze the existing 'config.yaml', 'initial_program.py', and 'evaluator.py' files instead of re-initializing.", break_loop=False)

            try:
                target_full_path.mkdir(parents=True, exist_ok=True)
                required_files = ["config.yaml", "initial_program.py", "evaluator.py", "test_evaluator.py"]
                
                for file_name in required_files:
                    src_file = source_skeleton / file_name
                    if src_file.exists():
                        shutil.copy2(src_file, target_full_path / file_name)
                        
                msg = [
                    f"✅ Evolutionary project successfully initialized at: {target_full_path}",
                    "Generated Files:",
                    "  - config.yaml       (Evolution parameters & LLM settings)",
                    "  - initial_program.py (Target function to optimize)",
                    "  - evaluator.py       (Fitness function & multi-objective scoring)",
                    "  - test_evaluator.py  (Validation script for your evaluator)",
                    "\nNext Step: Configure your settings in config.yaml and start the engine."
                ]
                return Response(message="\n".join(msg), break_loop=False)
                
            except Exception as e:
                return Response(message=f"❌ Initialization Error: {str(e)}", break_loop=False)

        elif action == "run":
            project_path = self.args.get("path", os.getcwd())
            max_iterations = self.args.get("max_iterations")
            output_dir = self.args.get("output")
            checkpoint_path = self.args.get("checkpoint")
            
            p = Path(project_path)
            init_prog = p / "initial_program.py"
            eval_file = p / "evaluator.py"
            conf_file = p / "config.yaml"
            
            # --- 1. STRICT FILE VALIDATION ---
            missing_files = []
            if not init_prog.exists(): missing_files.append("initial_program.py")
            if not eval_file.exists(): missing_files.append("evaluator.py")
            if not conf_file.exists(): missing_files.append("config.yaml")
            
            if missing_files:
                msg = f"❌ Error: Required files missing in '{project_path}': {', '.join(missing_files)}\n\n"
                msg += "⚠️ Strict Naming Rules:\n"
                msg += "- The program to be optimized MUST be named 'initial_program.py'.\n"
                msg += "- The evaluation logic MUST be contained in 'evaluator.py'.\n"
                msg += "- The configuration settings MUST be provided in 'config.yaml'.\n\n"
                msg += "💡 Tip: Use the 'init' action to generate a fresh project skeleton:\n"
                msg += f"human-skills '{{\"tool_name\": \"OpenevolveTool\", \"tool_args\": {{\"action\": \"init\", \"project_dir\": \"{p.name}\"}}}}'"
                return Response(message=msg, break_loop=False)

            # --- 2. CHECKPOINT VALIDATION ---
            if checkpoint_path:
                chk = Path(checkpoint_path)
                if not chk.exists():
                    msg = (
                        f"❌ Error: Checkpoint path '{checkpoint_path}' does not exist.\n"
                        "💡 Guidance:\n"
                        "- Checkpoints are not available for new evolution runs.\n"
                        "- Ensure the checkpoint name is correct and corresponds to a previous run of this project.\n"
                        "- Only previously evolved programs with stored states possess valid checkpoints."
                    )
                    return Response(message=msg, break_loop=False)

            # --- 3. CONSTRUCT COMMAND ---
            cmd = ["openevolve-run", str(init_prog), str(eval_file), "--config", str(conf_file)]
            if max_iterations:
                cmd += ["--iterations", str(max_iterations)]
            if output_dir:
                cmd += ["--output", str(output_dir)]
            if checkpoint_path:
                cmd += ["--checkpoint", str(checkpoint_path)]
                
            try:
                print(f"[*] Starting OpenEvolve Engine: {' '.join(cmd)}")
                process = subprocess.run(cmd, capture_output=True, text=True)
                
                if process.returncode == 0:
                    return Response(message=f"✅ Evolution session completed successfully.\n\n{process.stdout}", break_loop=False)
                else:
                    return Response(message=f"❌ Evolution engine returned an error:\n\n{process.stderr}\n{process.stdout}", break_loop=False)
            except Exception as e:
                return Response(message=f"❌ Execution Error: {str(e)}", break_loop=False)

        elif action == "list_example":
            base_dir = Path(__file__).parent.parent / "openevolve" / "examples"
            if not base_dir.exists():
                return Response(message=f"❌ Error: Local examples directory not found at {base_dir}.", break_loop=False)

            # Filter examples that have BOTH evaluator.py and config.yaml
            valid_examples = []
            if base_dir.exists():
                for d in base_dir.iterdir():
                    if d.is_dir() and not d.name.startswith("__"):
                        if (d / "evaluator.py").exists() and (d / "config.yaml").exists():
                            valid_examples.append(d.name)
            
            valid_examples.sort()
            msg = "✅ Verified OpenEvolve Examples:\n" + "="*40 + "\n"
            msg += "\n".join([f"  - {ex}" for ex in valid_examples])
            msg += "\n" + "="*40 + "\n"
            msg += "💡 Tip: Use 'show_example' with 'example_view' to see code details."
            return Response(message=msg, break_loop=False)

        elif action == "show_example":
            example_name = self.args.get("example_view")
            if not example_name:
                return Response(message="❌ Error: 'example_view' argument is required for this action.", break_loop=False)

            base_dir = Path(__file__).parent.parent / "openevolve" / "examples" / example_name

            if not base_dir.exists():
                return Response(message=f"❌ Error: Example '{example_name}' not found.", break_loop=False)

            # Read contents
            eval_path = base_dir / "evaluator.py"
            conf_path = base_dir / "config.yaml"
            
            output = [f"✅ Example: {example_name}", "="*60]
            if eval_path.exists():
                output.append(f"\n--- [ evaluator.py ] ---\n{eval_path.read_text()}")
            if conf_path.exists():
                output.append(f"\n--- [ config.yaml ] ---\n{conf_path.read_text()}")
            
            return Response(message="\n".join(output), break_loop=False)

        else:
            return Response(message=f"❌ Unknown action: {action}", break_loop=False)