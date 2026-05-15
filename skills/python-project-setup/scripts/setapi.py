import shutil
from pathlib import Path
from helpers.tool import Tool, Response

class SetApi(Tool):
    """
    Scaffolds the FastAPI middleware stack into any project.
    Copies error_handlers.py, middleware.py, and cors.py from resources/api/.
    Only overwrites files that share the same name — never touches other existing files.
    """
    name: str = "setapi"
    description: str = "Scaffolds FastAPI middleware stack (error handlers, request-id, security headers, CORS) into the target project."
    arguments: dict = {
        "destination": "Target path where API middleware should be created (e.g. '/path/to/project/src/api').",
        "override": "Optional boolean ('true' or 'false'). If true, overwrites existing matching files."
    }
    instruction: str = "Use this tool to set up the FastAPI middleware stack in a new or existing project."

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(message="❌ Error: 'destination' argument is required.", break_loop=False)

        dest_path = Path(dest_str).resolve()

        override_str = str(self.args.get("override", "false")).lower()
        override = override_str in ("true", "1", "yes", "y")

        resources_dir = Path(__file__).resolve().parent.parent / "resources" / "api"
        if not resources_dir.exists():
            return Response(message=f"❌ Error: api resources not found at {resources_dir}", break_loop=False)

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

            msg = f"✅ API middleware scaffolded successfully at: {dest_path}\n"
            if copied_files:
                msg += f"📄 Copied files: {', '.join(sorted(copied_files))}\n"
            if skipped_files:
                msg += f"⏭️ Skipped files (already exist): {', '.join(sorted(skipped_files))}\n"
                msg += "💡 Use 'override': 'true' to force overwrite matching files.\n"

            msg += "\n📋 Next steps:\n"
            msg += "  1. Add to main.py:\n"
            msg += "     from src.api.error_handlers import register_error_handlers\n"
            msg += "     from src.api.middleware import register_middleware\n"
            msg += "     from src.api.cors import register_cors\n"
            msg += "  2. Call after creating FastAPI app:\n"
            msg += "     register_cors(app, Settings)\n"
            msg += "     register_middleware(app, logger, Settings)\n"
            msg += "     register_error_handlers(app, logger)\n"

            return Response(message=msg, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Error scaffolding API middleware: {str(e)}", break_loop=False)
