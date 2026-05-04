import re
from typing import Any
from helpers.tool import Tool

SCHEMA_VALIDATORS = re.compile(
    r'\b(BaseModel|pydantic|Schema|Serializer|ModelSerializer|'
    r'marshmallow|Cerberus|jsonschema|voluptuous|schematics|'
    r'attrs|dataclasses|TypedDict|'
    r'validate\(|is_valid\(|\.validate\b|deserialize\(|'
    r'Joi\.|Yup\.|Zod\.|z\.|validator\.)\b',
    re.IGNORECASE,
)

MANUAL_CHECKS = re.compile(
    r'\b(isinstance\(|type\s*\(|len\s*\(.*\).*[<>]|'
    r'\.strip\(\)|\.isdigit\(\)|\.isalpha\(\)|'
    r'raise\s+ValueError|raise\s+ValidationError|'
    r'assert\s+|re\.match\(|re\.fullmatch\(|re\.compile\()\b',
    re.IGNORECASE,
)

ORM_USAGE = re.compile(
    r'\b(\.filter\(|\.get\(|\.create\(|\.update\(|\.objects\.|'
    r'session\.query|db\.session|Model\.query)\b',
    re.IGNORECASE,
)

RAW_SQL_UNSAFE = re.compile(
    r'(f["\'].*SELECT.*{|f["\'].*INSERT.*{|f["\'].*UPDATE.*{|'
    r'f["\'].*DELETE.*{|%s.*%.*\(|format\(.*SELECT|'
    r'execute\s*\(\s*f["\']|execute\s*\(\s*".*\+)',
    re.IGNORECASE,
)

PARAMETERISED_SQL = re.compile(
    r'execute\s*\(\s*["\'][^"\']*\?[^"\']*["\']'  # SQLite ? style
    r'|execute\s*\(\s*["\'][^"\']*%s[^"\']*["\']'  # DB-API %s style
    r'|execute\s*\(\s*["\'][^"\']*:[\w]+[^"\']*["\']',  # named params
    re.IGNORECASE,
)

XSS_PREVENTION = re.compile(
    r'\b(escape\(|html\.escape|bleach\.|markupsafe|'
    r'sanitize|sanitise|DOMPurify|encodeHTML|htmlspecialchars)\b',
    re.IGNORECASE,
)

FILE_UPLOAD_VALIDATION = re.compile(
    r'\b(allowed_extensions|ALLOWED_EXTENSIONS|secure_filename|'
    r'mimetype|content_type.*image|content_type.*pdf|'
    r'file\.filename|\.endswith\(\s*["\'])\b',
    re.IGNORECASE,
)

REQUEST_SIZE_LIMIT = re.compile(
    r'\b(MAX_CONTENT_LENGTH|max_upload_size|content_length|'
    r'body_size_limit|request\.content_length|'
    r'max_body_size|body_limit)\b',
    re.IGNORECASE,
)


class InputValidation(Tool):
    def __init__(self):
        super().__init__(
            name="input_validation",
            description=(
                "Scores input validation practices in REST API code: checks for schema validators "
                "(Pydantic/Marshmallow), manual checks, SQL injection prevention, XSS protection, "
                "file upload validation, and request size limits."
            )
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        score = 0.0

        # 1. Schema-level validation (0.30) — most important
        if SCHEMA_VALIDATORS.search(source_code):
            score += 0.30

        # 2. Manual type/range checks (0.15)
        manual_count = len(MANUAL_CHECKS.findall(source_code))
        if manual_count >= 3:
            score += 0.15
        elif manual_count > 0:
            score += 0.08

        # 3. ORM usage (0.15) — implicit SQL injection protection
        uses_orm = bool(ORM_USAGE.search(source_code))
        uses_raw_sql = bool(RAW_SQL_UNSAFE.search(source_code))
        uses_parameterised = bool(PARAMETERISED_SQL.search(source_code))

        if uses_orm or uses_parameterised:
            score += 0.15
        elif uses_raw_sql:
            score -= 0.25   # String-interpolated SQL — strong penalty

        # 4. XSS prevention (0.15)
        if XSS_PREVENTION.search(source_code):
            score += 0.15

        # 5. File upload validation (0.15) — only if uploads are present
        has_upload = re.search(r'\b(file|upload|multipart|FormData)\b', source_code, re.I)
        if has_upload:
            if FILE_UPLOAD_VALIDATION.search(source_code):
                score += 0.15
            else:
                score -= 0.10   # File upload with no validation

        # 6. Request size limit (0.10)
        if REQUEST_SIZE_LIMIT.search(source_code):
            score += 0.10

        return round(min(max(score, 0.0), 1.0), 4)