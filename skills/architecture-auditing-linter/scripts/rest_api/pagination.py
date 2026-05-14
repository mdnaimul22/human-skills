import re
from typing import Any
from helpers.tool import Tool

PAGINATION_PARAMS = re.compile(
    r'\b(limit|offset|page|page_size|per_page|page_num|cursor|after|before|'
    r'skip|take|start|count|size|from_id|last_id)\b',
    re.IGNORECASE,
)

CURSOR_SIGNALS = re.compile(
    r'\b(cursor|keyset|after_cursor|before_cursor|next_cursor|last_evaluated_key|'
    r'continuation_token|scroll_id)\b',
    re.IGNORECASE,
)

# Pagination metadata in response
RESPONSE_METADATA = re.compile(
    r'\b(total|total_count|total_pages|has_more|has_next|has_prev|'
    r'next_page|prev_page|next_url|prev_url|links|meta|pagination|'
    r'x-total-count|x-page)\b',
    re.IGNORECASE,
)

# Signals that a collection of items is being returned (increases relevance)
COLLECTION_SIGNALS = re.compile(
    r'\b(all|list|find|filter|query|fetchall|select|where|scan)\s*\('
    r'|\.(objects\.all|items|results|records)\b',
    re.IGNORECASE,
)

# Anti-patterns: fetching without any limit
UNLIMITED_FETCH = re.compile(
    r'\.(all|fetchall|find|query|select|scan)\s*\(\s*\)',
    re.IGNORECASE,
)

# ORM limit calls
LIMIT_APPLIED = re.compile(
    r'\.(limit\(|take\(|paginate\(|slice\(|LIMIT\s+\d)',
    re.IGNORECASE,
)

# Query param extraction patterns (framework-agnostic)
QUERY_PARAM_ACCESS = re.compile(
    r'request\.(args|query|GET|params)\s*[\.\[](.*?)["\'\]]'
    r'|params\[["\'](\w+)["\']\]'
    r'|query\.(\w+)',
    re.IGNORECASE,
)


def _is_collection_endpoint(source_code: str) -> bool:
    """Quick check: does this code appear to return a list of resources?"""
    return bool(COLLECTION_SIGNALS.search(source_code))


class PaginationImplementation(Tool):
    def __init__(self):
        super().__init__(
            name="pagination_implementation",
            description=(
                "Scores whether REST API list endpoints implement pagination correctly: "
                "checks for limit/offset or cursor parameters, response metadata, and "
                "absence of unbounded collection fetches."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        # If the code doesn't return collections, pagination is not required
        if not _is_collection_endpoint(source_code):
            return 1.0, []   # N/A — neutral pass

        score = 0.0
        suggestions = []

        # 1. Pagination parameters present (0.35)
        has_pagination_params = bool(PAGINATION_PARAMS.search(source_code))
        if has_pagination_params:
            score += 0.35
        else:
            suggestions.append("Extract pagination parameters (e.g., limit, offset, page, cursor) from incoming requests.")

        # 2. Cursor-based pagination (bonus on top of param check) (0.10)
        has_cursor = bool(CURSOR_SIGNALS.search(source_code))
        if has_cursor:
            score += 0.10

        # 3. Limit is actually applied to the query (0.25)
        has_limit = bool(LIMIT_APPLIED.search(source_code))
        if has_limit:
            score += 0.25
        else:
            suggestions.append("Apply a strict LIMIT to database/ORM queries to prevent fetching the entire collection into memory.")

        # 4. Response includes pagination metadata (0.20)
        has_metadata = bool(RESPONSE_METADATA.search(source_code))
        if has_metadata:
            score += 0.20
        else:
            suggestions.append("Include pagination metadata in the response (e.g., total_count, has_next, next_cursor) to aid client navigation.")

        # 5. No unbounded fetches detected (0.10 bonus, or penalty)
        unlimited_count = len(UNLIMITED_FETCH.findall(source_code))
        if unlimited_count == 0:
            score += 0.10
        else:
            score -= 0.15 * unlimited_count  # penalise each unbounded fetch
            suggestions.append("CRITICAL: Unbounded collection fetch detected (e.g. .all() without limit). This will crash under high load.")

        if score < 0.8 and not suggestions:
             suggestions.append("Improve pagination logic by adding limit constraints and response metadata.")

        return round(min(max(score, 0.0), 1.0), 4), suggestions