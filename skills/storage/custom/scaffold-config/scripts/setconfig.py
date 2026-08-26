import shutil
from pathlib import Path
from helpers.tool import Tool, Response

class SetConfig(Tool):
    """
    Scaffolds the canonical src/config/ layer into any Python project.
    Copies all files from the resources/ directory to the specified destination.
    """
    name: str = "setconfig"
    description: str = "Scaffolds standard config layer (paths, files, dotenv, settings, logger) into the target project."
    arguments: dict = {
        "destination": "Target path where the 'config/' directory should be created (e.g. '/path/to/project/src/config').",
        "override": "Optional boolean ('true' or 'false'). If true, overwrites existing config files."
    }
    instruction: str = "Use this tool to set up the canonical src/config/ layer in a new or existing Python project."

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(message="❌ Error: 'destination' argument is required.", break_loop=False)

        dest_path = Path(dest_str).resolve()
        
        override_str = str(self.args.get("override", "false")).lower()
        override = override_str in ("true", "1", "yes", "y")

        resources_dir = Path(__file__).resolve().parent.parent / "resources" / "config"
        if not resources_dir.exists():
            return Response(message=f"❌ Error: resources directory not found at {resources_dir}", break_loop=False)

        try:
            dest_path.mkdir(parents=True, exist_ok=True)
            copied_files = []
            skipped_files = []

            for src_file in resources_dir.glob("*.py"):
                dst_file = dest_path / src_file.name
                
                if dst_file.exists() and not override:
                    skipped_files.append(src_file.name)
                    continue

                shutil.copy2(src_file, dst_file)
                copied_files.append(src_file.name)

            msg = f"✅ Configuration scaffolded successfully at: {dest_path}\n"
            if copied_files:
                msg += f"📄 Copied files: {', '.join(copied_files)}\n"
            if skipped_files:
                msg += f"⏭️ Skipped files (already exist): {', '.join(skipped_files)}\n"
                msg += "💡 Use 'override': 'true' to force overwrite."

            return Response(message=msg, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Error scaffolding config: {str(e)}", break_loop=False)