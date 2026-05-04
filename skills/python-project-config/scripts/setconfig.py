import shutil
from pathlib import Path
from helpers.tool import Tool, Response


class SetConfig(Tool):
    """
    Scaffolds the canonical src/config/ layer into any Python project.
    Copies all files from the resources/ directory to the specified destination.
    """

    name: str = "setconfig"
    description: str = (
        "Copies the canonical src/config/ template (paths.py, files.py, dotenv.py, "
        "settings.py, logger.py, __init__.py) into a target project directory. "
        "Use this to bootstrap any new Python project with the standard config layer."
    )
    arguments: dict = {
        "destination": "Absolute path to the target config directory (e.g. /home/user/my_project/src/config). REQUIRED.",
        "override": "Set to 'true' to overwrite existing files. Defaults to 'false' (safe mode — skips existing files).",
    }
    instruction: str = (
        "Run this tool when starting a new Python project to scaffold the standard "
        "src/config/ layer automatically. After scaffolding, add project-specific "
        "fields to settings.py and fill in .env from .env.example."
    )

    # The canonical resource files live next to this script
    _RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"

    async def execute(self, **kwargs) -> Response:
        destination_str = self.args.get("destination")
        if not destination_str:
            return Response(
                message=(
                    "❌ Error: 'destination' argument is required.\n"
                    "💡 Usage: human-skills '{\"tool_name\": \"setconfig\", "
                    "\"tool_args\": {\"destination\": \"/path/to/your_project/src/config\"}}'"
                ),
                break_loop=False,
            )

        override = str(self.args.get("override", "false")).strip().lower() == "true"
        destination = Path(destination_str).resolve()

        # Validate resources dir
        if not self._RESOURCES_DIR.exists():
            return Response(
                message=f"❌ Internal error: resources directory not found at '{self._RESOURCES_DIR}'.",
                break_loop=False,
            )

        # Create destination if it doesn't exist
        destination.mkdir(parents=True, exist_ok=True)

        # Copy each resource file
        resource_files = list(self._RESOURCES_DIR.glob("*.py"))
        if not resource_files:
            return Response(
                message="❌ Internal error: No resource files found to copy.",
                break_loop=False,
            )

        copied   = []
        skipped  = []

        for src_file in sorted(resource_files):
            dest_file = destination / src_file.name
            if dest_file.exists() and not override:
                skipped.append(src_file.name)
                continue
            shutil.copy2(src_file, dest_file)
            copied.append(src_file.name)

        # Build report
        status_icon = "✨" if not skipped else "⚠️"
        msg  = f"🚀 SetConfig — scaffolding config layer\n"
        msg += "=" * 55 + "\n"
        msg += f"📁 Destination : {destination}\n"
        msg += f"🔄 Override    : {'yes' if override else 'no (safe mode)'}\n"
        msg += "=" * 55 + "\n"

        if copied:
            msg += "\n✅ Copied:\n"
            for f in copied:
                msg += f"   • {f}\n"

        if skipped:
            msg += "\n⏭️  Skipped (already exist):\n"
            for f in skipped:
                msg += f"   • {f}\n"
            msg += "\n💡 Tip: Use override=true to overwrite existing files.\n"

        msg += "\n" + "=" * 55 + "\n"

        if copied:
            msg += f"{status_icon} Done! {len(copied)} file(s) scaffolded into {destination.name}/\n"
            msg += "\n📋 Next steps:\n"
            msg += "   1. Add project-specific fields to settings.py\n"
            msg += "   2. Copy .env.example → .env and fill in mandatory values\n"
            msg += "   3. Use 'from src.config import Settings, setup_logger' anywhere\n"
        else:
            msg += "ℹ️  Nothing was copied — all files already exist. Use override=true to force.\n"

        return Response(message=msg, break_loop=False)
