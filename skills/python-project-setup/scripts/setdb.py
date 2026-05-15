import shutil
from pathlib import Path
from helpers.tool import Tool, Response

class SetDb(Tool):
    """
    Scaffolds the async SQLAlchemy database layer into any project.
    Copies __init__.py, connection.py, and repository.py from resources/db/.
    Only overwrites files that share the same name — never touches other existing files.
    """
    name: str = "setdb"
    description: str = "Scaffolds async SQLAlchemy database layer (connection management, base CRUD repository) into the target project."
    arguments: dict = {
        "destination": "Target path where DB layer should be created (e.g. '/path/to/project/src/helpers').",
        "override": "Optional boolean ('true' or 'false'). If true, overwrites existing matching files."
    }
    instruction: str = "Use this tool to set up the async database layer in a new or existing project."

    async def execute(self, **kwargs) -> Response:
        dest_str = self.args.get("destination")
        if not dest_str:
            return Response(message="❌ Error: 'destination' argument is required.", break_loop=False)

        dest_path = Path(dest_str).resolve()

        override_str = str(self.args.get("override", "false")).lower()
        override = override_str in ("true", "1", "yes", "y")

        resources_dir = Path(__file__).resolve().parent.parent / "resources" / "db"
        if not resources_dir.exists():
            return Response(message=f"❌ Error: db resources not found at {resources_dir}", break_loop=False)

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

            msg = f"✅ Database layer scaffolded successfully at: {dest_path}\n"
            if copied_files:
                msg += f"📄 Copied files: {', '.join(sorted(copied_files))}\n"
            if skipped_files:
                msg += f"⏭️ Skipped files (already exist): {', '.join(sorted(skipped_files))}\n"
                msg += "💡 Use 'override': 'true' to force overwrite matching files.\n"

            msg += "\n📋 Next steps:\n"
            msg += "  1. Install: pip install 'sqlalchemy[asyncio]' aiosqlite  (or asyncpg for PostgreSQL)\n"
            msg += "  2. Add DATABASE_URL to .env and Settings:\n"
            msg += "     DATABASE_URL=sqlite+aiosqlite:///./data/app.db\n"
            msg += "  3. Call init_db(Settings.DATABASE_URL) in FastAPI lifespan\n"
            msg += "     (from src.helpers.connection import init_db)\n"
            msg += "  4. Create model-specific repositories extending BaseRepository\n"
            msg += "     (from src.helpers.repository import BaseRepository)\n"

            return Response(message=msg, break_loop=False)

        except Exception as e:
            return Response(message=f"❌ Error scaffolding database layer: {str(e)}", break_loop=False)
