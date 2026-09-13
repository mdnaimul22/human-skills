import ast
import re
from typing import List, Set

from default.security import SecurityDetector, SecurityIssue, HIGH, MEDIUM


class InfoDisclosureDetector(SecurityDetector):
    """Detects debug modes, traceback exposure, timing attacks, and auth misuse."""

    name = "info_disclosure"
    description = "Detects debug=True, traceback exposure, sensitive logging, timing attacks, and assert-for-auth."

    SENSITIVE_NAMES = {
        'password', 'passwd', 'secret', 'token',
        'api_key', 'private_key', 'auth', 'credential'
    }
    AUTH_KEYWORDS = {
        'admin', 'auth', 'perm', 'role', 'access',
        'login', 'verified', 'authorized'
    }

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node))
            elif isinstance(node, ast.Compare):
                issues.extend(self._check_timing_attack(node))
            elif isinstance(node, ast.Assert):
                issues.extend(self._check_assert_auth(node))

        # Regex: sensitive data in print/logging
        for match in re.finditer(
            r'(?:print|logging\.(?:info|debug|warning|error))\s*\(.*(?:password|secret|token|api_key|private_key)',
            source_code, re.IGNORECASE
        ):
            line = source_code[:match.start()].count('\n') + 1
            issues.append(SecurityIssue(
                MEDIUM, line, "sensitive_data_logged",
                "Sensitive data potentially logged — mask or remove from log output."
            ))

        return issues

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _extract_sensitive_names(self, node: ast.expr) -> Set[str]:
        """
        Recursively extract identifier names from a node.
        Handles: ast.Name, ast.Attribute, ast.Call (func name),
                 ast.Subscript, ast.Compare operands.

        Examples caught:
            password                    → ast.Name
            user.password               → ast.Attribute
            request.headers.get("token")→ ast.Call  (func.attr)
            data["secret"]              → ast.Subscript (slice Constant)
        """
        names: Set[str] = set()

        if isinstance(node, ast.Name):
            names.add(node.id.lower())

        elif isinstance(node, ast.Attribute):
            names.add(node.attr.lower())
            # also check the object (e.g. user.password → 'user', 'password')
            names |= self._extract_sensitive_names(node.value)

        elif isinstance(node, ast.Call):
            # e.g. request.headers.get("token") → attr = 'get', but check args too
            names |= self._extract_sensitive_names(node.func)
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    names.add(arg.value.lower())

        elif isinstance(node, ast.Subscript):
            # data["secret"] → slice is a Constant string
            if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
                names.add(node.slice.value.lower())
            names |= self._extract_sensitive_names(node.value)

        return names

    def _check_call(self, node: ast.Call) -> List[SecurityIssue]:
        results = []

        if not isinstance(node.func, ast.Attribute):
            return results

        func = node.func.attr

        # Debug mode: app.run(debug=True)
        if func == 'run':
            for kw in node.keywords:
                if kw.arg == 'debug' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    results.append(SecurityIssue(
                        MEDIUM, node.lineno, "debug_mode",
                        "'debug=True' in production exposes interactive debugger and sensitive info."
                    ))

        # traceback exposure
        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'traceback':
            if func in ('print_exc', 'format_exc', 'print_exception', 'format_exception'):
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "stack_trace_exposure",
                    f"'traceback.{func}()' may expose internal paths and code structure."
                ))

        # tempfile.mktemp() — deprecated, race condition
        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'tempfile':
            if func == 'mktemp':
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "tempfile_race",
                    "'tempfile.mktemp()' is deprecated — race condition vulnerability. Use tempfile.mkstemp()."
                ))

        return results

    def _check_timing_attack(self, node: ast.Compare) -> List[SecurityIssue]:
        """
        Detect == / != comparison on sensitive variable names.

        Now handles:
            password == input_pass              (ast.Name)
            user.password == input_pass         (ast.Attribute)
            request.headers.get("token") == x  (ast.Call)
            data["secret"] == value             (ast.Subscript)
        """
        if not (len(node.ops) == 1 and isinstance(node.ops[0], (ast.Eq, ast.NotEq))):
            return []

        # Collect all names from left and all comparators
        all_names: Set[str] = self._extract_sensitive_names(node.left)
        for comp in node.comparators:
            all_names |= self._extract_sensitive_names(comp)

        if all_names & self.SENSITIVE_NAMES:
            return [SecurityIssue(
                MEDIUM, node.lineno, "timing_attack",
                "Direct '==' comparison on sensitive value — use 'hmac.compare_digest()'."
            )]

        return []

    def _check_assert_auth(self, node: ast.Assert) -> List[SecurityIssue]:
        """Detect assert used for auth/security checks."""
        results = []

        if isinstance(node.test, ast.Attribute):
            if any(kw in node.test.attr.lower() for kw in self.AUTH_KEYWORDS):
                results.append(SecurityIssue(
                    HIGH, node.lineno, "assert_for_security",
                    f"'assert' used for security check ({node.test.attr}) — "
                    "assert removed with python -O. Use if/raise instead."
                ))
        elif isinstance(node.test, ast.Call) and isinstance(node.test.func, ast.Name):
            if any(kw in node.test.func.id.lower() for kw in self.AUTH_KEYWORDS):
                results.append(SecurityIssue(
                    HIGH, node.lineno, "assert_for_security",
                    f"'assert {node.test.func.id}()' — assert removed with -O flag. Use if/raise."
                ))

        return results