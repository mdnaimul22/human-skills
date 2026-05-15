import shutil
from pathlib import Path
from helpers.tool import Tool, Response

class SetHelpers(Tool):
    """
    Scaffolds universal helper utilities into any Python project.
    Copies exceptions.py, date_utils.py, and retry.py from resources/helpers/.
    Only overwrites files that share the same name — never touches other existing files.
    """
    name: str = "sethelpers"
    description: str = "Scaffolds universal helpers (exceptions, date_utils, retry) into the target project's helpers directory."
    arguments: dict = {
        "destination": "Target path where helpers should be created (e.g. '/path/to/project/src/helpers').",
        "override": "Optional boolean ('true' or 'false'). If true, overwrites existing matching files."
    }
    instruction: str = "Use this tool to set up universal helper utilities in a new or existing Python project."

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(message="❌ Error: 'destination' argument is required.", break_loop=False)

        dest_path = Path(dest_str).resolve()

        override_str = str(self.args.get("override", "false")).lower()
        override = override_str in ("true", "1", "yes", "y")

        resources_dir = Path(__file__).resolve().parent.parent / "resources" / "helpers"
        if not resources_dir.exists():
            return Response(message=f"❌ Error: helpers resources not found at {resources_dir}", break_loop=False)

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

            msg = f"✅ Helpers scaffolded successfully at: {dest_path}\n"
            if copied_files:
                msg += f"📄 Copied files: {', '.join(sorted(copied_files))}\n"
            if skipped_files:
                msg += f"⏭️ Skipped files (already exist): {', '.join(sorted(skipped_files))}\n"
                msg += "💡 Use 'override': 'true' to force overwrite matching files.\n"

            msg += "\n📋 Next steps:\n"
            msg += "  1. Rename AppError → YourProjectError in exceptions.py (optional)\n"
            msg += "  2. Add 'tenacity' to your dependencies for retry.py\n"
            msg += "  3. Import: from src.helpers.exceptions import AppError, NotFoundError\n"

            return Response(message=msg, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Error scaffolding helpers: {str(e)}", break_loop=False)
