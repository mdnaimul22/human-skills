import ast
import re
from typing import List
from urllib.parse import urlparse

from default.security import SecurityDetector, SecurityIssue, MEDIUM, LOW


class NetworkDetector(SecurityDetector):
    name = "network"
    description = "Detects SSRF, 0.0.0.0 binding, unvalidated redirects, and plaintext HTTP."

    SAFE_NAMESPACE_HOSTS = {
        "www.w3.org", "w3.org", "schemas.openxmlformats.org", "schemas.xmlsoap.org",
        "purl.org", "xmlns.com", "ns.adobe.com", "ogp.me", "schema.org", "example.com",
    }
    SAFE_REDIRECT_BUILDERS = {"url_for", "reverse", "reverse_lazy"}
    WEB_REDIRECT_MODULES = {"flask", "django", "shortcuts", "web", "responses", "starlette", "fastapi"}
    _PRIVATE_IP_RE = re.compile(r"^(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)")

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []
        docstring_ids = self._collect_docstring_ids(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node))
            elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docstring_ids:
                issues.extend(self._check_plaintext_http(node))

        return issues

    @staticmethod
    def _collect_docstring_ids(tree: ast.AST) -> set[int]:
        ids: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant):
                    if isinstance(node.body[0].value.value, str):
                        ids.add(id(node.body[0].value))
        return ids

    def _is_safe_http_host(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            host = (parsed.hostname or "").lower()
        except ValueError:
            return True
        if not host or host in {"localhost", "127.0.0.1", "0.0.0.0", "::1", "host.docker.internal"}:
            return True
        if host in self.SAFE_NAMESPACE_HOSTS:
            return True
        if self._PRIVATE_IP_RE.match(host):
            return True
        if "." not in host:
            return True
        return False

    def _check_plaintext_http(self, node: ast.Constant) -> List[SecurityIssue]:
        val = node.value.strip()
        if not val.startswith("http://") or "{" in val:
            return []
        if self._is_safe_http_host(val):
            return []
        return [SecurityIssue(
            LOW, node.lineno, "plaintext_http",
            "Plaintext HTTP URL — use HTTPS to prevent traffic interception."
        )]

    def _is_trusted_config_url(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, ast.Name) and node.id.isupper():
            return True
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            if node.value.id == "Settings":
                return True
            if node.value.id in ("self", "cls") and any(k in node.attr.lower() for k in ("base_url", "api_url", "endpoint")):
                return True
        if isinstance(node, ast.JoinedStr) and node.values:
            first = node.values[0]
            if isinstance(first, ast.FormattedValue) and self._is_trusted_config_url(first.value):
                return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if self._is_trusted_config_url(node.left):
                return True
        return False

    def _is_dynamic_url(self, node: ast.expr) -> bool:
        if self._is_trusted_config_url(node):
            return False
        return isinstance(node, (
            ast.Name,
            ast.BinOp,
            ast.JoinedStr,
            ast.Call,
            ast.Attribute,
            ast.Subscript,
        ))

    def _is_safe_redirect_target(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, ast.Name) and node.id.isupper():
            return True
        if isinstance(node, ast.Call):
            fn = node.func.id if isinstance(node.func, ast.Name) else (
                node.func.attr if isinstance(node.func, ast.Attribute) else ""
            )
            if fn in self.SAFE_REDIRECT_BUILDERS:
                return True
        return False

    def _check_call(self, node: ast.Call) -> List[SecurityIssue]:
        results = []

        if not isinstance(node.func, ast.Attribute):
            return results
        if not isinstance(node.func.value, ast.Name):
            return results

        mod = node.func.value.id
        func = node.func.attr

        if mod == 'requests' and func in ('get', 'post', 'put', 'delete', 'head', 'patch', 'request'):
            if node.args and self._is_dynamic_url(node.args[0]):
                url_type = self._describe_url_node(node.args[0])
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "ssrf",
                    f"'requests.{func}()' with dynamic URL ({url_type}) — "
                    "validate or allowlist URLs to prevent SSRF."
                ))

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

        if func == 'redirect' and mod.lower() in self.WEB_REDIRECT_MODULES and node.args:
            if not self._is_safe_redirect_target(node.args[0]) and self._is_dynamic_url(node.args[0]):
                results.append(SecurityIssue(
                    MEDIUM, node.lineno, "open_redirect",
                    "Redirect with dynamic URL — validate destination to prevent open redirect attacks."
                ))

        return results

    def _describe_url_node(self, node: ast.expr) -> str:
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
