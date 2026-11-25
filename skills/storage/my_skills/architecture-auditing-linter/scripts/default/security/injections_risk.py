import ast
import re
from typing import List, Set

from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH, MEDIUM, LOW


class InjectionDetector(SecurityDetector):
    name = "injection"
    description = "Detects command, code, SQL, template, LDAP, XML, XPath, CRLF, and log injection risks."

    DANGEROUS_CALLS = {'eval', 'exec', 'compile', '__import__'}

    CMD_EXEC_PATTERNS = {
        ('os', 'system'), ('os', 'popen'), ('os', 'popen2'), ('os', 'popen3'),
        ('os', 'popen4'), ('os', 'execl'), ('os', 'execle'), ('os', 'execlp'),
        ('os', 'execv'), ('os', 'execve'), ('os', 'execvp'), ('os', 'execvpe'),
        ('os', 'spawnl'), ('os', 'spawnle'), ('commands', 'getoutput'),
        ('commands', 'getstatusoutput'),
    }

    TEMPLATE_PATTERNS = {
        ('jinja2', 'Template'),
        ('jinja2', 'from_string'),
        ('mako', 'Template'),
    }

    XML_PARSE_IMPORTS = {'parse', 'fromstring', 'fromstringlist', 'iterparse', 'XML', 'XMLID', 'XMLParser', 'XMLPullParser'}

    _SQL_CLAUSE_RE = re.compile(
        r"\b(?:"
        r"SELECT\b.+\bFROM\b"
        r"|INSERT\s+INTO\b"
        r"|UPDATE\s+\w+\s+SET\b"
        r"|DELETE\s+FROM\b"
        r"|DROP\s+(?:TABLE|DATABASE|INDEX|VIEW|SCHEMA)\b"
        r"|ALTER\s+(?:TABLE|DATABASE|SCHEMA)\b"
        r"|TRUNCATE\s+(?:TABLE\s+)?\w+"
        r"|CREATE\s+(?:TABLE|DATABASE|INDEX|VIEW|SCHEMA)\b"
        r"|UNION\s+(?:ALL\s+)?SELECT\b"
        r")",
        re.IGNORECASE | re.DOTALL,
    )

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        self._issues: List[SecurityIssue] = []
        self._shadowed_builtins: Set[str] = self._collect_shadowed_builtins(tree)
        self._has_safe_lxml = "resolve_entities=False" in source_code
        self._visit_tree(tree)
        self._detect_sql_injection_ast(tree)
        self._detect_crlf_ast(tree)
        return self._issues

    def _collect_shadowed_builtins(self, tree: ast.AST) -> Set[str]:
        shadowed: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module != "builtins":
                for alias in node.names:
                    bound = alias.asname or alias.name
                    if bound in self.DANGEROUS_CALLS:
                        shadowed.add(bound)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in self.DANGEROUS_CALLS:
                    shadowed.add(node.name)
        return shadowed

    def _visit_tree(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                self._check_call(node)
            elif isinstance(node, ast.ImportFrom):
                self._check_import(node)

    def _check_call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in self.DANGEROUS_CALLS:
            if node.func.id not in self._shadowed_builtins:
                self._issues.append(SecurityIssue(
                    CRITICAL, node.lineno, "code_injection",
                    f"'{node.func.id}()' allows arbitrary code execution."
                ))

        if not isinstance(node.func, ast.Attribute):
            return

        func = node.func.attr

        if func == 'format_map' and not isinstance(node.func.value, ast.Constant):
            self._issues.append(SecurityIssue(
                MEDIUM, node.lineno, "format_injection",
                "'str.format_map()' on dynamic template — potential information disclosure via __class__."
            ))

        if not isinstance(node.func.value, ast.Name):
            return

        mod = node.func.value.id

        if (mod, func) in self.CMD_EXEC_PATTERNS:
            self._issues.append(SecurityIssue(
                HIGH, node.lineno, "command_injection",
                f"'{mod}.{func}()' — potential command injection. Use subprocess with shell=False."
            ))

        if mod == 'subprocess' and func in ('call', 'run', 'Popen', 'check_output', 'check_call'):
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._issues.append(SecurityIssue(
                        HIGH, node.lineno, "command_injection",
                        f"'subprocess.{func}()' with shell=True — vulnerable to shell injection."
                    ))

        if (mod, func) in self.TEMPLATE_PATTERNS:
            if node.args and not isinstance(node.args[0], ast.Constant):
                self._issues.append(SecurityIssue(
                    HIGH, node.lineno, "template_injection",
                    "Template created from variable — potential SSTI (Server-Side Template Injection)."
                ))

        if func == 'xpath' and node.args and not isinstance(node.args[0], ast.Constant):
            arg = node.args[0]
            if not (isinstance(arg, ast.Name) and arg.id.isupper()):
                self._issues.append(SecurityIssue(
                    MEDIUM, node.lineno, "xpath_injection",
                    "XPath query built from variable — potential XPath injection."
                ))

        if mod == 'ldap' and func in ('search', 'search_s', 'search_ext'):
            self._issues.append(SecurityIssue(
                MEDIUM, node.lineno, "ldap_injection",
                "LDAP search with potentially unsanitized filter — use ldap3.utils.filter_escape()."
            ))

    def _check_import(self, node: ast.ImportFrom) -> None:
        if node.module in ('xml.etree.ElementTree', 'xml.dom.minidom', 'xml.sax'):
            imported_names = {a.name for a in node.names}
            if "*" in imported_names or (imported_names & self.XML_PARSE_IMPORTS) or node.module != 'xml.etree.ElementTree':
                self._issues.append(SecurityIssue(
                    MEDIUM, node.lineno, "xxe",
                    f"'{node.module}' is vulnerable to XXE attacks. Use 'defusedxml' instead."
                ))
        if node.module and node.module == 'lxml.etree' and not self._has_safe_lxml:
            self._issues.append(SecurityIssue(
                LOW, node.lineno, "xxe",
                f"'{node.module}' — ensure resolve_entities=False and no_network=True."
            ))

    def _render_expr_template(self, node: ast.expr) -> tuple[str, bool]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value, False
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            has_dynamic = False
            for val in node.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                else:
                    parts.append("__VAR__")
                    has_dynamic = True
            return "".join(parts), has_dynamic
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
            left_s, left_d = self._render_expr_template(node.left)
            right_s, right_d = self._render_expr_template(node.right)
            return f"{left_s}{right_s}", True if isinstance(node.op, ast.Mod) else (left_d or right_d)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            base_s, _ = self._render_expr_template(node.func.value)
            return base_s, bool(node.args or node.keywords)
        return "__VAR__", True

    def _check_sql_expr(self, expr: ast.expr, lineno: int) -> None:
        if isinstance(expr, ast.JoinedStr):
            rendered, has_dynamic = self._render_expr_template(expr)
            if has_dynamic and self._SQL_CLAUSE_RE.search(rendered):
                self._issues.append(SecurityIssue(
                    HIGH, lineno, "sql_injection",
                    "SQL query built with f-string — use parameterized queries (cursor.execute(sql, params))."
                ))
        elif isinstance(expr, ast.BinOp) and isinstance(expr.op, (ast.Add, ast.Mod)):
            rendered, has_dynamic = self._render_expr_template(expr)
            if has_dynamic and self._SQL_CLAUSE_RE.search(rendered):
                op_type = "% formatting" if isinstance(expr.op, ast.Mod) else "string concatenation"
                self._issues.append(SecurityIssue(
                    HIGH, lineno, "sql_injection",
                    f"SQL query built with {op_type} — use parameterized queries."
                ))
        elif isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "format":
            rendered, has_dynamic = self._render_expr_template(expr)
            if has_dynamic and self._SQL_CLAUSE_RE.search(rendered):
                self._issues.append(SecurityIssue(
                    HIGH, lineno, "sql_injection",
                    "SQL query built with .format() — use parameterized queries."
                ))

    def _detect_sql_injection_ast(self, tree: ast.AST) -> None:
        checked_expr_ids: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'execute' and node.args:
                query_arg = node.args[0]
                checked_expr_ids.add(id(query_arg))
                self._check_sql_expr(query_arg, node.lineno)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and id(node.value) not in checked_expr_ids:
                self._check_sql_expr(node.value, node.lineno)
            elif isinstance(node, ast.AnnAssign) and node.value and id(node.value) not in checked_expr_ids:
                self._check_sql_expr(node.value, node.lineno)

    def _detect_crlf_ast(self, tree: ast.AST) -> None:
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Subscript):
                        target_str = ast.unparse(target.value).lower()
                        if "header" in target_str:
                            rendered, has_dynamic = self._render_expr_template(node.value)
                            if has_dynamic and ("\r\n" in rendered or "\\r\\n" in rendered):
                                self._issues.append(SecurityIssue(
                                    MEDIUM, node.lineno, "crlf_injection",
                                    "Potential CRLF injection in header value."
                                ))
