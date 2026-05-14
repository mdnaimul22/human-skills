"""
Tool: Timeout Handling Score
Category: Reliability
Evaluates whether REST API code properly handles timeouts for:
- Outbound HTTP requests (requests.get timeout= param)
- Database query timeouts
- Async operation timeouts (asyncio.wait_for, anyio)
- Connection pool timeouts
- Endpoint-level response timeout / deadline propagation
"""
import re
from typing import Any
from helpers.tool import Tool

HTTP_CLIENT_TIMEOUT = re.compile(
    r'\b(requests\.(get|post|put|delete|patch|request|Session)\s*\([^)]*timeout\s*=|'
    r'httpx\.(get|post|put|delete|patch|request|AsyncClient|Client)\s*\([^)]*timeout\s*=|'
    r'aiohttp\.ClientTimeout|ClientTimeout\s*\(|'
    r'urllib\.request\.(urlopen|Request).*timeout|'
    r'Timeout\s*\(|connect_timeout|read_timeout|write_timeout)\b',
    re.IGNORECASE | re.DOTALL,
)

HTTP_CLIENT_MISSING_TIMEOUT = re.compile(
    r'\b(requests\.(get|post|put|delete|patch)\s*\(["\'](?!.*timeout))',
    re.IGNORECASE,
)

DB_TIMEOUT = re.compile(
    r'\b(connect_timeout|command_timeout|query_timeout|'
    r'pool_timeout|connection_timeout|execution_timeout|'
    r'statement_timeout|lock_timeout|'
    r'socket_timeout|TIMEOUT\s*=\s*\d)\b',
    re.IGNORECASE,
)

ASYNC_TIMEOUT = re.compile(
    r'\b(asyncio\.wait_for\s*\(|asyncio\.timeout\s*\(|'
    r'anyio\.fail_after\s*\(|anyio\.move_on_after\s*\(|'
    r'async_timeout\.|timeout_at\(|shield\s*\()\b',
    re.IGNORECASE,
)

CONNECTION_POOL_TIMEOUT = re.compile(
    r'\b(pool_timeout|pool_recycle|pool_pre_ping|'
    r'max_overflow|pool_size.*timeout|'
    r'QueuePool.*timeout|NullPool|StaticPool)\b',
    re.IGNORECASE,
)

DEADLINE_PROPAGATION = re.compile(
    r'\b(grpc_timeout|deadline|context\.deadline|'
    r'X-Request-Timeout|Request-Timeout|timeout_seconds|'
    r'propagate.*timeout|timeout.*header)\b',
    re.IGNORECASE,
)

TIMEOUT_ERROR_HANDLING = re.compile(
    r'\b(TimeoutError|ReadTimeout|ConnectTimeout|'
    r'requests\.exceptions\.Timeout|httpx\.TimeoutException|'
    r'asyncio\.TimeoutError|socket\.timeout|'
    r'except.*Timeout|504|GATEWAY_TIMEOUT)\b',
    re.IGNORECASE,
)

# Anti-pattern: explicit no-timeout (timeout=None or timeout=0 with no override)
NO_TIMEOUT_EXPLICIT = re.compile(
    r'timeout\s*=\s*None(?!\s*\).*default)',
    re.IGNORECASE,
)

MAKES_EXTERNAL_CALLS = re.compile(
    r'\b(requests\.|httpx\.|aiohttp\.|urllib\.|http\.client\.|grpc\.)\b',
    re.IGNORECASE,
)

MAKES_DB_CALLS = re.compile(
    r'\b(session\.|db\.|cursor\.|engine\.|Model\.objects)\b',
    re.IGNORECASE,
)


class TimeoutHandling(Tool):
    def __init__(self):
        super().__init__(
            name="timeout_handling",
            description=(
                "Scores timeout handling in REST API code: checks for timeouts on outbound HTTP "
                "requests, database queries, async operations, connection pools, and proper "
                "timeout error handling."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        makes_http   = bool(MAKES_EXTERNAL_CALLS.search(source_code))
        makes_db     = bool(MAKES_DB_CALLS.search(source_code))

        # If code makes no external calls and no DB calls, timeouts are N/A
        if not makes_http and not makes_db:
            return 0.8   # Not applicable — generous neutral score

        score = 0.0

        # 1. HTTP client timeout (0.30) — most critical
        if makes_http:
            if HTTP_CLIENT_TIMEOUT.search(source_code):
                score += 0.30
            else:
                score -= 0.20  # External calls with no timeout = reliability risk

        # 2. DB timeout configured (0.20)
        if makes_db:
            if DB_TIMEOUT.search(source_code):
                score += 0.20
            else:
                score -= 0.05

        # 3. Async timeout (0.20)
        has_async = re.search(r'\b(async def|await )\b', source_code)
        if has_async:
            if ASYNC_TIMEOUT.search(source_code):
                score += 0.20
            else:
                score -= 0.05   # Async without timeout gates

        # 4. Connection pool timeout (0.10)
        if CONNECTION_POOL_TIMEOUT.search(source_code):
            score += 0.10

        # 5. Timeout error handling (0.15)
        if TIMEOUT_ERROR_HANDLING.search(source_code):
            score += 0.15

        # 6. Deadline propagation (0.05 bonus)
        if DEADLINE_PROPAGATION.search(source_code):
            score += 0.05

        # Penalty for explicit timeout=None
        no_timeout_count = len(NO_TIMEOUT_EXPLICIT.findall(source_code))
        score -= no_timeout_count * 0.10

        return round(min(max(score, 0.0), 1.0), 4)