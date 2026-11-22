import re
from urllib.parse import unquote
from src.apps.waf.schema import ThreatCategory, RuleMatch

_RULES: tuple[tuple[str, ThreatCategory, str, float, str, re.Pattern[str]], ...] = (
    ("SQLi-1", ThreatCategory.SQL_INJECTION, "high", 80.0, "sql_keywords", re.compile(
        r"(?i)(union(\s|%20)+select|drop(\s|%20)+table|insert(\s|%20)+into|delete(\s|%20)+from|;\s*--|\bor(\s|%20)+1=1\b)"
    )),
    ("SQLi-2", ThreatCategory.SQL_INJECTION, "critical", 90.0, "db_functions", re.compile(
        r"(?i)(exec(\s|%20)+\(|xp_cmdshell|sp_executesql|pg_exec)"
    )),
    ("XSS-1", ThreatCategory.XSS, "high", 70.0, "xss_scripts", re.compile(
        r"(?i)(<script|%3Cscript|onerror=|onload=|alert\(|javascript:|eval\s*\()"
    )),
    ("XSS-2", ThreatCategory.XSS, "medium", 50.0, "html_embed", re.compile(
        r"(?i)(<iframe|<object|<embed|data:text/html)"
    )),
    ("CMD-1", ThreatCategory.COMMAND_INJECTION, "critical", 95.0, "shell_commands", re.compile(
        r"(?i)([;&|`]\s*(ls|cat|pwd|whoami|id|uname|wget|curl|nc|netcat))"
    )),
    ("PATH-1", ThreatCategory.PATH_TRAVERSAL, "high", 75.0, "dir_traversal", re.compile(
        r"(?i)(\.\./|\.\.\\|/etc/passwd|/proc/self|/windows/system32)"
    )),
    ("RCE-1", ThreatCategory.RCE, "critical", 100.0, "eval_execution", re.compile(
        r"(?i)(eval\s*\(|exec\s*\(|system\s*\(|shell_exec|passthru)"
    )),
    ("RCE-2", ThreatCategory.RCE, "critical", 90.0, "template_jndi", re.compile(
        r"(?i)(\$\{.*\}|jndi:|ldap://|rmi://|dns://|\{\{.*\}\})"
    )),
    ("XXE-1", ThreatCategory.XXE, "high", 80.0, "xml_entity", re.compile(
        r"(?i)(<!ENTITY|<!DOCTYPE|SYSTEM\s+['\"]|PUBLIC\s+['\"]|file://|php://|expect://)"
    )),
    ("SSRF-1", ThreatCategory.SSRF, "high", 75.0, "internal_endpoints", re.compile(
        r"(?i)(http://127\.0\.0\.1|http://localhost|http://0\.0\.0\.0|http://169\.254|gopher://|dict://)"
    )),
    ("LFI-1", ThreatCategory.LFI, "high", 85.0, "file_wrappers", re.compile(
        r"(?i)(\.\./|\.\.\\|include\s*\(|require\s*\(|php://|data://)"
    )),
    ("SCANNER-1", ThreatCategory.SCANNER, "high", 90.0, "automated_scanner", re.compile(
        r"(?i)(wafw00f|sqlmap|nikto|acunetix|dirbuster|nmap|masscan|zgrab|nessus|openvas|hydra|burpsuite)"
    )),
    ("HONEYPOT-1", ThreatCategory.HONEYPOT, "high", 85.0, "honeypot_probe", re.compile(
        r"(?i)(\.(php|env|git|yaml|yml|bak|asp|aspx|jsp|cgi|sh|bash|rb|py|pl|cfg|ini|log|sql|db|sqlite)$"
        r"|wp-admin|wp-login|phpmyadmin|actuator|cgi-bin|passwd|shadow|\.htaccess"
        r"|/aws|/config|/mysql|/_ignition|/xmlrpc|/solr|/jenkins|/jmx-console)"
    )),
)

_ALLOWED_PREFIXES: tuple[str, ...] = (
    "/api/v1/",
    "/health",
    "/docs",
    "/openapi.json",
    "/_next/",
    "/favicon",
    "/static/",
)

class RuleEngine:
    def __init__(self, allowed_prefixes: tuple[str, ...] = _ALLOWED_PREFIXES) -> None:
        self._allowed_prefixes = allowed_prefixes

    def is_allowed_path(self, path: str) -> bool:
        return path == "/" or path.startswith(self._allowed_prefixes)

    def match(self, text: str) -> list[RuleMatch]:
        decoded = unquote(unquote(text))
        matches: list[RuleMatch] = []
        for rule_id, category, severity, score, pattern_name, pattern in _RULES:
            if pattern.search(text) or pattern.search(decoded):
                matches.append(RuleMatch(
                    rule_id=rule_id,
                    category=category,
                    severity=severity,
                    score=score,
                    pattern_name=pattern_name,
                ))
        return matches
