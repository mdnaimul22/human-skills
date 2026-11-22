import sys
from pathlib import Path


class ProjectBoundary(Path):
    def safe_resolve(self, incoming_path: str | Path) -> Path:
        raw_str = str(incoming_path).strip()
        if not raw_str:
            raise ValueError("Path cannot be empty or whitespace")
        if "\0" in raw_str:
            raise ValueError("Null bytes not permitted in path")

        p = Path(raw_str).expanduser()
        resolved = (p if p.is_absolute() else self / p).resolve()

        try:
            resolved.relative_to(self)
        except ValueError:
            raise ValueError(f"Access denied: path '{incoming_path}' escapes sandbox ({self})")

        return resolved

    @classmethod
    def detect(cls, start: Path | None = None) -> "ProjectBoundary":
        current = (start or Path(__file__)).resolve()
        current = current.parent if current.is_file() else current
        for parent in [current, *current.parents]:
            if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
                return cls(parent)
        return cls(current.parent)


PROJECT_ROOT = ProjectBoundary.detect()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
