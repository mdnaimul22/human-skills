import ast
import re
from typing import List

from default.security import SecurityDetector, SecurityIssue, HIGH, MEDIUM, LOW


class NetworkDetector(SecurityDetector):
    """Detects SSRF, insecure bindings, and network misconfigurations."""

    name = "network"
    description = "Detects SSRF, 0.0.0.0 binding, unvalidated redirects, and plaintext HTTP."

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node))

        # Plaintext HTTP URLs (excluding localhost/internal)
        for match in re.finditer(
            r'["\']http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^"\']+["\']',
            source_code
        ):
            line = source_code[:match.start()].count('\n') + 1
            issues.append(SecurityIssue(
                LOW, line, "plaintext_http",
                "Plaintext HTTP URL — use HTTPS to prevent traffic interception."
            ))

        return issues

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    def _is_dynamic_url(self, node: ast.expr) -> bool:
        """
        Returns True if the URL argument is dynamic (non-constant).

        Handles:
            variable                        → ast.Name
            base_url + "/api"               → ast.BinOp
            f"https://{host}/path"          → ast.JoinedStr  (f-string)
            config.get("url")               → ast.Call
            user.url / request.url          → ast.Attribute
            urls[0]                         → ast.Subscript
        """
        # Constant string → safe (hardcoded URL, not user-controlled)
        if isinstance(node, ast.Constant):
            return False

        # Any of the dynamic types
        return isinstance(node, (
            ast.Name,        # variable
            ast.BinOp,       # "https://" + host
            ast.JoinedStr,   # f"https://{host}/path"
            ast.Call,        # config.get("url"), request.args.get("url")
            ast.Attribute,   # user.url, self.base_url
            ast.Subscript,   # urls[0], data["url"]
        ))

    def _check_call(self, node: ast.Call) -> List[SecurityIssue]:
        results = []

        if not isinstance(node.func, ast.Attribute):
            return results
        if not isinstance(node.func.value, ast.Name):
            return results

        mod  = node.func.value.id
        func = node.func.attr

        # ── SSRF: requests.get/post/... with dynamic URL ──
        if mod == 'requests' and func in ('get', 'post', 'put', 'delete', 'head', 'patch', 'request'):
            if node.args and self._is_dynamic_url(node.args[0]):
                url_type = self._describe_url_node(node.args[0])
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "ssrf",
                    f"'requests.{func}()' with dynamic URL ({url_type}) — "
                    "validate or allowlist URLs to prevent SSRF."
                ))

        # ── socket.bind to 0.0.0.0 ──
        if func == 'bind':
            for arg in node.args:
                if isinstance(arg, ast.Tuple) and arg.elts:
                    first = arg.elts[0]
                    if isinstance(first, ast.Constant) and first.value == '0.0.0.0':
                        results.append(SecurityIssue(
                            MEDIUM, node.lineno, "insecure_binding",
                            "Binding to '0.0.0.0' exposes service on all interfaces. "
                            "Bind to a specific IP in production."
                        ))

        # ── Unvalidated redirect ──
        if func == 'redirect' and node.args and self._is_dynamic_url(node.args[0]):
            results.append(SecurityIssue(
                MEDIUM, node.lineno, "open_redirect",
                "Redirect with dynamic URL — validate destination to prevent open redirect attacks."
            ))

        return results

    def _describe_url_node(self, node: ast.expr) -> str:
        """Return a human-readable description of the dynamic URL node type."""
        if isinstance(node, ast.Name):
            return f"variable '{node.id}'"
        if isinstance(node, ast.BinOp):
            return "string concatenation"
        if isinstance(node, ast.JoinedStr):
            return "f-string"
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                return f"call to '{node.func.attr}()'"
            return "function call"
        if isinstance(node, ast.Attribute):
            return f"attribute '{node.attr}'"
        if isinstance(node, ast.Subscript):
            return "subscript access"
        return "dynamic expression"