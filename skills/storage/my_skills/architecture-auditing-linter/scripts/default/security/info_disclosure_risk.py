import ast
import re
from typing import List, Set

from default.security import SecurityDetector, SecurityIssue, HIGH, MEDIUM


class InfoDisclosureDetector(SecurityDetector):
    name = "info_disclosure"
    description = "Detects debug modes, traceback exposure, sensitive logging, timing attacks, and assert-for-auth."

    SENSITIVE_NAMES = {
        'password', 'passwd', 'secret', 'token',
        'api_key', 'private_key', 'credential', 'secret_key',
        'access_token', 'refresh_token', 'auth_token', 'client_secret',
    }
    SENSITIVE_LOG_TOKENS = {
        'password', 'passwd', 'secret', 'token', 'api_key', 'apikey', 'private_key', 'credential',
    }
    NON_SECRET_SUFFIXES = (
        '_count', '_len', '_length', '_id', '_type', '_kind', '_status',
        '_url', '_path', '_ttl', '_expiry', '_expired', '_name', '_header',
        '_mode', '_format', '_prefix', '_scheme', '_source', '_scope',
    )
    AUTH_KEYWORDS = {
        'admin', 'auth', 'perm', 'perms', 'permission', 'permissions',
        'role', 'roles', 'access', 'login', 'verified', 'authorized',
    }
    WEB_RUNNERS = {'app', 'application', 'flask_app', 'server', 'web', 'api', 'sanic', 'quart', 'bottle'}
    LOG_FUNCS = {'info', 'debug', 'warning', 'error', 'critical', 'exception', 'warn'}
    LOG_OBJECTS = {'logging', 'logger', 'log'}
    _TOKEN_SPLIT_RE = re.compile(r"[_\s]+|(?<=[a-z])(?=[A-Z])")

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []
        logged_traceback_ids = self._collect_logged_traceback_ids(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node, logged_traceback_ids))
                issues.extend(self._check_sensitive_logging(node))
            elif isinstance(node, ast.Compare):
                issues.extend(self._check_timing_attack(node))
            elif isinstance(node, ast.Assert):
                issues.extend(self._check_assert_auth(node))

        return issues

    def _collect_logged_traceback_ids(self, tree: ast.AST) -> Set[int]:
        ids: Set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and self._is_logger_call(node):
                for arg in node.args:
                    for sub in ast.walk(arg):
                        if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                            if isinstance(sub.func.value, ast.Name) and sub.func.value.id == "traceback":
                                ids.add(id(sub))
        return ids

    def _is_logger_call(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Attribute) and node.func.attr in self.LOG_FUNCS:
            if isinstance(node.func.value, ast.Name) and node.func.value.id.lower() in self.LOG_OBJECTS:
                return True
            if isinstance(node.func.value, ast.Attribute) and node.func.value.attr.lower() in self.LOG_OBJECTS:
                return True
        return False

    def _is_print_or_log_call(self, node: ast.Call) -> bool:
        if isinstance(node.func, ast.Name) and node.func.id == "print":
            return True
        return self._is_logger_call(node)

    def _is_sensitive_identifier(self, name: str) -> bool:
        low = name.lower()
        if low.endswith(self.NON_SECRET_SUFFIXES):
            return False
        if low in self.SENSITIVE_NAMES:
            return True
        tokens = set(low.split("_"))
        return bool(tokens & self.SENSITIVE_LOG_TOKENS)

    def _extract_logged_expr_names(self, node: ast.expr) -> Set[str]:
        names: Set[str] = set()
        if isinstance(node, ast.Constant):
            return names
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            if not node.attr.lower().endswith(self.NON_SECRET_SUFFIXES):
                names.add(node.attr.lower())
        elif isinstance(node, ast.JoinedStr):
            for val in node.values:
                if isinstance(val, ast.FormattedValue):
                    names |= self._extract_logged_expr_names(val.value)
        elif isinstance(node, ast.BinOp):
            names |= self._extract_logged_expr_names(node.left)
            names |= self._extract_logged_expr_names(node.right)
        elif isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                names.add(node.slice.value.lower())
            names |= self._extract_logged_expr_names(node.value)
        elif isinstance(node, (ast.Tuple, ast.List)):
            for elt in node.elts:
                names |= self._extract_logged_expr_names(elt)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
                for a in node.args:
                    names |= self._extract_logged_expr_names(a)
                for kw in node.keywords:
                    names |= self._extract_logged_expr_names(kw.value)
            else:
                for a in node.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str):
                        if a.value.lower() in self.SENSITIVE_NAMES:
                            names.add(a.value.lower())
                    else:
                        names |= self._extract_logged_expr_names(a)
        return names

    def _check_sensitive_logging(self, node: ast.Call) -> List[SecurityIssue]:
        if not self._is_print_or_log_call(node):
            return []
        found: Set[str] = set()
        for arg in node.args:
            found |= self._extract_logged_expr_names(arg)
        for kw in node.keywords:
            found |= self._extract_logged_expr_names(kw.value)
        if any(self._is_sensitive_identifier(n) for n in found):
            return [SecurityIssue(
                MEDIUM, node.lineno, "sensitive_data_logged",
                "Sensitive data potentially logged — mask or remove from log output."
            )]
        return []

    def _extract_compare_sensitive_names(self, node: ast.expr) -> Set[str]:
        names: Set[str] = set()
        if isinstance(node, ast.Name):
            names.add(node.id.lower())
        elif isinstance(node, ast.Attribute):
            attr_low = node.attr.lower()
            if attr_low in self.NON_SECRET_SUFFIXES or attr_low in {"type", "kind", "scope", "status", "expired", "name", "id"}:
                return names
            names.add(attr_low)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == "get":
                for arg in node.args[:1]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        names.add(arg.value.lower())
        elif isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                names.add(node.slice.value.lower())
        return names

    @staticmethod
    def _is_trivial_literal(node: ast.expr) -> bool:
        if isinstance(node, ast.Constant):
            return node.value is None or isinstance(node.value, (bool, int, float)) or node.value == ""
        return False

    def _check_call(self, node: ast.Call, logged_traceback_ids: Set[int]) -> List[SecurityIssue]:
        results = []

        if not isinstance(node.func, ast.Attribute):
            return results

        func = node.func.attr
        caller = node.func.value.id.lower() if isinstance(node.func.value, ast.Name) else ""

        if func == 'run' and caller in self.WEB_RUNNERS:
            for kw in node.keywords:
                if kw.arg == 'debug' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    results.append(SecurityIssue(
                        MEDIUM, node.lineno, "debug_mode",
                        "'debug=True' in production exposes interactive debugger and sensitive info."
                    ))

        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'traceback':
            if func in ('print_exc', 'format_exc', 'print_exception', 'format_exception'):
                if id(node) not in logged_traceback_ids:
                    results.append(SecurityIssue(
                        MEDIUM, node.lineno, "stack_trace_exposure",
                        f"'traceback.{func}()' may expose internal paths and code structure."
                    ))

        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'tempfile':
            if func == 'mktemp':
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "tempfile_race",
                    "'tempfile.mktemp()' is deprecated — race condition vulnerability. Use tempfile.mkstemp()."
                ))

        return results

    def _check_timing_attack(self, node: ast.Compare) -> List[SecurityIssue]:
        if not (len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq))):
            return []

        if self._is_trivial_literal(node.left) or any(self._is_trivial_literal(c) for c in node.comparators):
            return []

        all_names: Set[str] = self._extract_compare_sensitive_names(node.left)
        for comp in node.comparators:
            all_names |= self._extract_compare_sensitive_names(comp)

        if all_names & self.SENSITIVE_NAMES:
            return [SecurityIssue(
                MEDIUM, node.lineno, "timing_attack",
                "Direct '==' comparison on sensitive value — use 'hmac.compare_digest()'."
            )]

        return []

    def _split_tokens(self, name: str) -> Set[str]:
        return {tok.lower() for tok in self._TOKEN_SPLIT_RE.split(name) if tok}

    def _check_assert_auth(self, node: ast.Assert) -> List[SecurityIssue]:
        results = []

        if isinstance(node.test, ast.Attribute):
            if self._split_tokens(node.test.attr) & self.AUTH_KEYWORDS:
                results.append(SecurityIssue(
                    HIGH, node.lineno, "assert_for_security",
                    f"'assert' used for security check ({node.test.attr}) — "
                    "assert removed with python -O. Use if/raise instead."
                ))
        elif isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Name):
            if self._split_tokens(node.test.func.id) & self.AUTH_KEYWORDS:
                results.append(SecurityIssue(
                    HIGH, node.lineno, "assert_for_security",
                    f"'assert {node.test.func.id}()' — assert removed with -O flag. Use if/raise."
                ))

        return results
