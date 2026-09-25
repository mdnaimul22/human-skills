import asyncio
import json
from pathlib import Path

import typer

from .collectors.registry import CollectorRegistry
from .engine import EvaluationEngine
from .judges.jev import JevJudge
from .models.candidate import Candidate
from .models.spec import EvaluationSpec

app = typer.Typer()


@app.command()
def evaluate(spec: Path, candidate_root: Path):
    s = EvaluationSpec.model_validate_json(spec.read_text())
    c = Candidate(
        candidate_id=candidate_root.name,
        root=candidate_root.resolve(),
        entrypoint="main.py",
        language="python",
    )
    engine = EvaluationEngine(collector_registry=CollectorRegistry.canonical(), judge=JevJudge())
    r = asyncio.run(engine.evaluate(c, s))
    typer.echo(json.dumps(r.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    app()
