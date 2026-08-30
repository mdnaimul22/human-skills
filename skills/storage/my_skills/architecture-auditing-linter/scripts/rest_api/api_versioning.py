import re
from typing import Any
from helpers.tool import Tool


# ── Versioning detection patterns ─────────────────────────────────────────────

# URL path versioning: /v1/, /v2/, /api/v3/ etc.
URL_VERSION_PATTERN = re.compile(
    r'["\'/](?:api/)?v(\d+)[/"\']',
    re.IGNORECASE,
)

# Version at root position: must be first meaningful segment
# e.g. @app.get("/v1/users") → v1 is at root ✅
# e.g. @app.get("/users/v1/active") → v1 is NOT at root ❌
VERSION_AT_ROOT = re.compile(
    r'["\']/(?:api/)?v\d+/',
    re.IGNORECASE,
)

# Version NOT at root — appears mid-path
VERSION_MID_PATH = re.compile(
    r'["\'][^"\']+/\w+/v\d+[/"\']',
    re.IGNORECASE,
)

# Header-based versioning signals
HEADER_VERSION_PATTERNS = re.compile(
    r'Accept-Version|'
    r'API-Version|'
    r'X-API-Version|'
    r'api[-_]version|'
    r'request\.version|'
    r'request\.headers\s*\[\s*["\'].*version.*["\']\s*\]',
    re.IGNORECASE,
)

# Query param versioning (less common, but valid)
QUERY_VERSION = re.compile(
    r'[\?&]v(?:ersion)?=\d+|'
    r'request\.(?:args|query_params|GET)\s*\.?\s*(?:get\s*\(\s*)?["\']v(?:ersion)?["\']',
    re.IGNORECASE,
)

# Media type versioning (application/vnd.myapi.v1+json)
MEDIA_TYPE_VERSION = re.compile(
    r'application/vnd\.\w+\.v\d+\+json|'
    r'Accept.*vnd\.\w+\.v\d+',
    re.IGNORECASE,
)

# Deprecation / sunset headers for old versions
SUNSET_HEADERS = re.compile(
    r'["\']Sunset["\']|'
    r'["\']Deprecation["\']|'
    r'deprecated\s*=\s*True|'
    r'@deprecated',
    re.IGNORECASE,
)

# Route decorator patterns to extract all endpoints
ROUTE_DECORATORS = re.compile(
    r'@\w+\.(get|post|put|delete|patch|route)\s*\(\s*["\']([^"\']+)["\']',
    re.IGNORECASE,
)


class ApiVersioningStrategy(Tool):
    def __init__(self):
        super().__init__(
            name="api_versioning",
            description=(
                "Scores API versioning strategy: checks for URL-based versioning, "
                "header versioning, version consistency across endpoints, version "
                "placement, and deprecation lifecycle headers."
            ),
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        score = 0.0
        suggestions = []

        # Extract all endpoints for consistency analysis
        endpoints = ROUTE_DECORATORS.findall(source_code)
        endpoint_paths = [path for _, path in endpoints]

        # Detect versioning strategies in use
        has_url_version = bool(URL_VERSION_PATTERN.search(source_code))
        has_header_version = bool(HEADER_VERSION_PATTERNS.search(source_code))
        has_query_version = bool(QUERY_VERSION.search(source_code))
        has_media_version = bool(MEDIA_TYPE_VERSION.search(source_code))

        strategies_count = sum([
            has_url_version,
            has_header_version,
            has_query_version,
            has_media_version,
        ])

        # No versioning at all
        if strategies_count == 0:
            suggestions.append(
                "No API versioning detected. Implement URL versioning "
                "(e.g., /v1/users) or header versioning (Accept-Version) "
                "to manage breaking changes safely."
            )
            # Still check sunset headers even without versioning
            if SUNSET_HEADERS.search(source_code):
                score += 0.15
            return round(score, 4), suggestions

        # 1. URL versioning detected (0.30)
        if has_url_version:
            score += 0.30

            # 2. Version at root position (0.20)
            root_versions = VERSION_AT_ROOT.findall(source_code)
            mid_versions = VERSION_MID_PATH.findall(source_code)
            if root_versions and not mid_versions:
                score += 0.20
            elif root_versions and mid_versions:
                score += 0.10
                suggestions.append(
                    "Inconsistent version placement: some endpoints have "
                    "version at root (/v1/users), others mid-path "
                    "(/users/v1/active). Standardize on root placement."
                )
            elif mid_versions:
                suggestions.append(
                    "API version appears mid-path. Place version prefix "
                    "at the root of the path: /v1/resource, not "
                    "/resource/v1/sub."
                )

        # 1b. Header versioning (0.30 if sole strategy, 0.15 as supplement)
        if has_header_version and not has_url_version:
            score += 0.30
            score += 0.20  # header = implicit root positioning
        elif has_header_version:
            score += 0.05  # supplementary to URL versioning

        # 1c. Query versioning (less desirable but valid)
        if has_query_version and not has_url_version and not has_header_version:
            score += 0.20
            suggestions.append(
                "Query parameter versioning (?v=1) is fragile — consider "
                "URL path (/v1/) or header versioning instead."
            )

        # 1d. Media type versioning
        if has_media_version:
            score += 0.10

        # 3. Consistency across endpoints (0.20)
        if endpoint_paths and has_url_version:
            versioned_paths = [p for p in endpoint_paths if URL_VERSION_PATTERN.search(f'"{p}"')]
            unversioned_paths = [p for p in endpoint_paths if not URL_VERSION_PATTERN.search(f'"{p}"')]

            if len(endpoint_paths) > 0:
                version_ratio = len(versioned_paths) / len(endpoint_paths)
                if version_ratio >= 0.8:
                    score += 0.20
                elif version_ratio >= 0.5:
                    score += 0.10
                    suggestions.append(
                        f"Only {len(versioned_paths)}/{len(endpoint_paths)} "
                        "endpoints are versioned. Apply versioning "
                        "consistently across all endpoints."
                    )
                else:
                    suggestions.append(
                        f"Only {len(versioned_paths)}/{len(endpoint_paths)} "
                        "endpoints have version prefixes. Most endpoints "
                        "are unversioned — this undermines the versioning strategy."
                    )

            # Check for multiple different versions (v1, v2, v3...)
            versions_found = set(URL_VERSION_PATTERN.findall(source_code))
            if len(versions_found) > 1:
                # Having multiple versions is fine — it means proper migration
                pass
        elif not has_url_version and has_header_version:
            # Header versioning — consistency is implicit
            score += 0.15

        # 4. Deprecation / sunset headers (0.15)
        if SUNSET_HEADERS.search(source_code):
            score += 0.15
        elif strategies_count > 0 and len(source_code) > 500:
            suggestions.append(
                "Add Sunset or Deprecation headers to old API versions "
                "to signal upcoming removals to clients."
            )

        # ── Penalty: Mixed strategies ─────────────────────────────────────────
        if strategies_count >= 3:
            score -= 0.20
            suggestions.append(
                "Too many versioning strategies detected (URL + header + "
                "query/media-type). Pick one primary strategy and stick "
                "with it."
            )
        elif has_url_version and has_query_version:
            score -= 0.10
            suggestions.append(
                "Mixing URL path versioning with query parameter versioning. "
                "Pick one strategy for consistency."
            )

        return round(min(max(score, 0.0), 1.0), 4), suggestions
