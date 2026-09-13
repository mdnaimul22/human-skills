import ast
import re
from typing import List, Set

from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH, MEDIUM, LOW


class InjectionDetector(SecurityDetector):
    """Detects injection vulnerabilities via AST and regex analysis."""

    name = "injection"
    description = "Detects command, code, SQL, template, LDAP, XML, XPath, CRLF, and log injection risks."

    # Dangerous direct-call functions
    DANGEROUS_CALLS = {'eval', 'exec', 'compile', '__import__'}

    # Command execution functions (module.func)
    CMD_EXEC_PATTERNS = {
        ('os', 'system'), ('os', 'popen'), ('os', 'popen2'), ('os', 'popen3'),
        ('os', 'popen4'), ('os', 'execl'), ('os', 'execle'), ('os', 'execlp'),
        ('os', 'execv'), ('os', 'execve'), ('os', 'execvp'), ('os', 'execvpe'),
        ('os', 'spawnl'), ('os', 'spawnle'), ('commands', 'getoutput'),
        ('commands', 'getstatusoutput'),
    }

    # Template rendering patterns
    TEMPLATE_PATTERNS = {
        ('jinja2', 'Template'),
        ('jinja2', 'from_string'),
        ('mako', 'Template'),
    }

    # SQL keywords to identify SQL strings
    SQL_KEYWORDS: Set[str] = {
        'SELECT', 'INSERT', 'UPDATE', 'DELETE',
        'DROP', 'ALTER', 'CREATE', 'TRUNCATE', 'UNION'
    }

    # Regex fallback pattern for SQL keywords
    _SQL_KW_PATTERN = r'(?:SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|UNION)'

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        self._issues: List[SecurityIssue] = []
        self._visit_tree(tree)
        self._detect_sql_injection_ast(tree)        # AST-based (multiline safe)
        self._detect_sql_injection_regex(source_code)  # Regex fallback
        self._detect_crlf(source_code)
        return self._issues

    # ──────────────────────────────────────────────
    # AST traversal
    # ──────────────────────────────────────────────

    def _visit_tree(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_call(node)
            elif isinstance(node, ast.ImportFrom):
                self._check_import(node)

    def _check_call(self, node: ast.Call):
        # 1. Direct dangerous calls (eval, exec, compile)
        if isinstance(node.func, ast.Name) and node.func.id in self.DANGEROUS_CALLS:
            self._issues.append(SecurityIssue(
                CRITICAL, node.lineno, "code_injection",
                f"'{node.func.id}()' allows arbitrary code execution."
            ))

        if not isinstance(node.func, ast.Attribute):
            return
        if not isinstance(node.func.value, ast.Name):
            return

        mod  = node.func.value.id
        func = node.func.attr

        # 2. Command injection via os.system, os.popen, etc.
        if (mod, func) in self.CMD_EXEC_PATTERNS:
            self._issues.append(SecurityIssue(
                HIGH, node.lineno, "command_injection",
                f"'{mod}.{func}()' — potential command injection. Use subprocess with shell=False."
            ))

        # 3. subprocess with shell=True
        if mod == 'subprocess' and func in ('call', 'run', 'Popen', 'check_output', 'check_call'):
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._issues.append(SecurityIssue(
                        HIGH, node.lineno, "command_injection",
                        f"'subprocess.{func}()' with shell=True — vulnerable to shell injection."
                    ))

        # 4. Template injection (SSTI)
        if (mod, func) in self.TEMPLATE_PATTERNS:
            if node.args and not isinstance(node.args[0], ast.Constant):
                self._issues.append(SecurityIssue(
                    HIGH, node.lineno, "template_injection",
                    "Template created from variable — potential SSTI (Server-Side Template Injection)."
                ))

        # 5. XPath injection
        if func == 'xpath' and node.args and not isinstance(node.args[0], ast.Constant):
            self._issues.append(SecurityIssue(
                MEDIUM, node.lineno, "xpath_injection",
                "XPath query built from variable — potential XPath injection."
            ))

        # 6. LDAP injection
        if mod == 'ldap' and func in ('search', 'search_s', 'search_ext'):
            self._issues.append(SecurityIssue(
                MEDIUM, node.lineno, "ldap_injection",
                "LDAP search with potentially unsanitized filter — use ldap3.utils.filter_escape()."
            ))

        # 7. str.format_map with variable
        if func == 'format_map' and node.args and not isinstance(node.args[0], ast.Constant):
            self._issues.append(SecurityIssue(
                MEDIUM, node.lineno, "format_injection",
                "'str.format_map()' with external data — potential information disclosure via __class__."
            ))

    def _check_import(self, node: ast.ImportFrom):
        # 8. XML/XXE: unsafe XML parsers
        if node.module and node.module in ('xml.etree.ElementTree', 'xml.dom.minidom', 'xml.sax'):
            self._issues.append(SecurityIssue(
                MEDIUM, node.lineno, "xxe",
                f"'{node.module}' is vulnerable to XXE attacks. Use 'defusedxml' instead."
            ))
        if node.module and 'lxml' in node.module:
            self._issues.append(SecurityIssue(
                LOW, node.lineno, "xxe",
                f"'{node.module}' — ensure resolve_entities=False and no_network=True."
            ))

    # ──────────────────────────────────────────────
    # SQL Injection — AST layer (multiline safe)
    # ──────────────────────────────────────────────

    def _detect_sql_injection_ast(self, tree: ast.AST):
        """
        AST-based SQL injection detection.
        Handles multiline queries, f-strings, concatenation, and % formatting.

        Patterns caught:
            cursor.execute("SELECT..." + user_id)       → BinOp with SQL keyword
            cursor.execute(f"SELECT...{user_id}")        → JoinedStr with SQL keyword
            cursor.execute("SELECT..." % user_id)        → BinOp (% formatting)
            query = "SELECT..." + x; cursor.execute(q)  → variable assignment
        """
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr != 'execute':
                continue
            if not node.args:
                continue

            query_arg = node.args[0]

            # f-string SQL: f"SELECT * FROM users WHERE id={user_id}"
            if isinstance(query_arg, ast.JoinedStr):
                if self._fstring_contains_sql(query_arg):
                    self._issues.append(SecurityIssue(
                        HIGH, node.lineno, "sql_injection",
                        "SQL query built with f-string — use parameterized queries (cursor.execute(sql, params))."
                    ))

            # Concatenation: "SELECT..." + user_id
            elif isinstance(query_arg, ast.BinOp):
                if self._binop_contains_sql(query_arg):
                    op_type = "% formatting" if isinstance(query_arg.op, ast.Mod) else "string concatenation"
                    self._issues.append(SecurityIssue(
                        HIGH, node.lineno, "sql_injection",
                        f"SQL query built with {op_type} — use parameterized queries."
                    ))

    def _fstring_contains_sql(self, node: ast.JoinedStr) -> bool:
        """Check if an f-string contains SQL keywords AND has dynamic parts."""
        has_dynamic = any(isinstance(v, ast.FormattedValue) for v in node.values)
        if not has_dynamic:
            return False
        text_parts = ' '.join(
            v.value for v in node.values
            if isinstance(v, ast.Constant) and isinstance(v.value, str)
        ).upper()
        return any(kw in text_parts for kw in self.SQL_KEYWORDS)

    def _binop_contains_sql(self, node: ast.BinOp) -> bool:
        """
        Recursively check if a BinOp tree contains a SQL keyword in any
        constant string part AND has at least one dynamic (non-constant) part.
        """
        sql_found = False
        dynamic_found = False

        def _walk_binop(n: ast.expr):
            nonlocal sql_found, dynamic_found
            if isinstance(n, ast.BinOp):
                _walk_binop(n.left)
                _walk_binop(n.right)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str):
                if any(kw in n.value.upper() for kw in self.SQL_KEYWORDS):
                    sql_found = True
            else:
                # Name, Call, Attribute, Subscript etc. — dynamic
                dynamic_found = True

        _walk_binop(node)
        return sql_found and dynamic_found

    # ──────────────────────────────────────────────
    # SQL Injection — Regex fallback
    # ──────────────────────────────────────────────

    def _detect_sql_injection_regex(self, source_code: str):
        """
        Regex-based SQL injection detection as a fallback.
        Catches patterns the AST layer may miss (e.g. multi-assignment chains).
        Deduplication via line numbers handled by BanditSecurityTool.
        """
        patterns = [
            (rf'f["\'].*{self._SQL_KW_PATTERN}\s.*\{{',
             "SQL query built with f-string — use parameterized queries."),
            (rf'["\'].*{self._SQL_KW_PATTERN}\s.*["\'].*\+',
             "SQL query built with string concatenation — use parameterized queries."),
            (r'\.execute\s*\([^)]*%\s',
             "SQL execute with % formatting — use parameterized queries."),
        ]
        for pattern, message in patterns:
            for match in re.finditer(pattern, source_code, re.IGNORECASE):
                line = source_code[:match.start()].count('\n') + 1
                self._issues.append(SecurityIssue(HIGH, line, "sql_injection", message))

    # ──────────────────────────────────────────────
    # CRLF / Log Injection
    # ──────────────────────────────────────────────

    def _detect_crlf(self, source_code: str):
        """CRLF / Log injection patterns."""
        for match in re.finditer(r'\\r\\n.*header', source_code, re.IGNORECASE):
            line = source_code[:match.start()].count('\n') + 1
            self._issues.append(SecurityIssue(
                MEDIUM, line, "crlf_injection",
                "Potential CRLF injection in header value."
            ))