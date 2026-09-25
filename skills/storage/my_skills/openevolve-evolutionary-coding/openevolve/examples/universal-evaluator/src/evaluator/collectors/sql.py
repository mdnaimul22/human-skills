import sqlite3
import time
from .base import EvidenceCollector
from .common import provenance
from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceStatus


class SQLCollector(EvidenceCollector):
    name = "sql"
    version = "1.0.0"

    async def collect(self, candidate, spec):
        cfg = spec.collector_config(self.name)
        if cfg is None:
            return []
        con = sqlite3.connect(cfg.database)
        out = []
        try:
            for sql in cfg.setup:
                con.executescript(sql)
            for i, query in enumerate(cfg.queries):
                started = time.perf_counter()
                ok = True
                rows = 0
                error = ""
                try:
                    rows = len(con.execute(query.sql).fetchall())
                    ok = query.expected_rows is None or rows == query.expected_rows
                except Exception as exc:
                    ok = False
                    error = str(exc)
                elapsed = (time.perf_counter() - started) * 1000
                out.append(Evidence(
                    id=f"sql-query-{i}", collector=self.name,
                    category=EvidenceCategory.CORRECTNESS,
                    status=EvidenceStatus.PASSED if ok else EvidenceStatus.FAILED,
                    value=1.0 if ok else 0.0, unit="pass", confidence=1,
                    metadata={"rows_returned": rows, "latency_ms": elapsed, "error": error},
                    duration_ms=elapsed,
                    provenance=provenance(candidate, self.version, ["sqlite", query.sql]),
                ))
        finally:
            con.close()
        return out
