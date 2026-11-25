import ast
import re
from typing import List, Set

from default.security import SecurityDetector, SecurityIssue, HIGH, MEDIUM, LOW


_ARCHIVE_MODULES = {'zipfile', 'tarfile', 'ZipFile', 'TarFile'}
_ARCHIVE_EXACT_NAMES = {'zf', 'tf', 'z', 'zipfile', 'tarfile', 'archive'}
_ARCHIVE_WORD_TOKENS = {'zip', 'tar', 'archive', 'zipfile', 'tarfile', 'zf', 'tf'}
_STREAM_VAR_NAMES = {'f', 'fp', 'fh', 'file', 'stream', 'stdin', 'pipe', 'sock', 'socket', 'raw', 'resp', 'response'}
_SAFE_TAR_FILTERS = {'data', 'tar'}


class ResourceDetector(SecurityDetector):
    name = "resource"
    description = "Detects ReDoS, zip bomb/slip, symlink attacks, unbounded read, and path traversal."

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []
        archive_vars: Set[str] = self._collect_archive_vars(tree)
        stream_vars: Set[str] = self._collect_stream_vars(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node, archive_vars, stream_vars))
                issues.extend(self._check_redos_call(node))
                issues.extend(self._check_path_traversal_call(node))

        return issues

    def _collect_archive_vars(self, tree: ast.AST) -> Set[str]:
        archive_vars: Set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        if self._is_archive_call(item.context_expr):
                            archive_vars.add(item.optional_vars.id)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if self._is_archive_call(node.value):
                            archive_vars.add(target.id)

        return archive_vars

    def _collect_stream_vars(self, tree: ast.AST) -> Set[str]:
        stream_vars: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        if self._is_stream_open_call(item.context_expr):
                            stream_vars.add(item.optional_vars.id)
            elif isinstance(node, ast.Assign):
                if self._is_stream_open_call(node.value):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            stream_vars.add(target.id)
        return stream_vars

    @staticmethod
    def _is_stream_open_call(node: ast.expr) -> bool:
        if not isinstance(node, ast.Call):
            return False
        if isinstance(node.func, ast.Name) and node.func.id == "open":
            return True
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("open", "urlopen"):
            return True
        return False

    def _is_archive_call(self, node: ast.expr) -> bool:
        if not isinstance(node, ast.Call):
            return False
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id in _ARCHIVE_MODULES:
                return True
        if isinstance(node.func, ast.Name) and node.func.id in _ARCHIVE_MODULES:
            return True
        return False

    def _check_call(self, node: ast.Call, archive_vars: Set[str], stream_vars: Set[str]) -> List[SecurityIssue]:
        results = []

        if not isinstance(node.func, ast.Attribute):
            return results

        func = node.func.attr
        caller_name = self._get_caller_name(node)

        if func == 'extractall':
            if self._is_archive_context(node, caller_name, archive_vars):
                has_filter = any(kw.arg in ('members', 'filter') for kw in node.keywords) or len(node.args) > 1
                if not has_filter:
                    results.append(SecurityIssue(
                        MEDIUM, node.lineno, "zip_bomb",
                        f"'{caller_name}.extractall()' without size validation — "
                        "vulnerable to zip bombs. Pass a 'members' generator that checks sizes."
                    ))

        if func == 'extract':
            if self._is_archive_context(node, caller_name, archive_vars):
                has_safe_filter = any(
                    kw.arg == 'filter' and isinstance(kw.value, ast.Constant) and kw.value.value in _SAFE_TAR_FILTERS
                    for kw in node.keywords
                )
                if not has_safe_filter:
                    results.append(SecurityIssue(
                        LOW, node.lineno, "zip_slip",
                        f"'{caller_name}.extract()' — verify extracted paths don't escape "
                        "the target directory (zip slip attack)."
                    ))

        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and func == 'symlink':
            results.append(SecurityIssue(
                MEDIUM, node.lineno, "symlink_attack",
                "'os.symlink()' — symlinks can be exploited to access unauthorized files."
            ))

        if func == 'read' and not node.args and not node.keywords:
            if caller_name in stream_vars or caller_name.lower() in _STREAM_VAR_NAMES:
                results.append(SecurityIssue(
                    LOW, node.lineno, "unbounded_read",
                    "'.read()' without size limit — may cause memory exhaustion with large data."
                ))

        return results

    def _is_archive_context(self, node: ast.Call, caller_name: str, archive_vars: Set[str]) -> bool:
        if caller_name in archive_vars:
            return True

        caller_lower = caller_name.lower()
        if caller_lower in _ARCHIVE_EXACT_NAMES:
            return True

        tokens = {tok for tok in re.split(r"[_\d]+", caller_lower) if tok}
        if tokens & _ARCHIVE_WORD_TOKENS:
            return True

        if isinstance(node.func.value, ast.Call):
            if self._is_archive_call(node.func.value):
                return True

        return False

    def _get_caller_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id
            if isinstance(node.func.value, ast.Attribute):
                return node.func.value.attr
        return "unknown"

    @staticmethod
    def _has_nested_quantifier(pattern: str) -> bool:
        for match in re.finditer(r'\((?:\?:)?([^()]+)\)\s*[+*]', pattern):
            inner = match.group(1)
            if not re.search(r'(?<!\\)[+*]', inner):
                continue
            if re.match(r'^(?:\\[.\-/:,;_]|[\-/:,;_])', inner):
                continue
            return True
        return False

    @staticmethod
    def _has_overlapping_alternation(pattern: str) -> bool:
        for match in re.finditer(r'\((?:\?:)?([^()]*\|[^()]*)\)\s*[+*]', pattern):
            branches = [b.strip() for b in match.group(1).split("|") if b.strip()]
            if len(branches) < 2:
                continue
            if len(set(branches)) < len(branches):
                return True
            if any(re.search(r'(?<!\\)[.+*]', b) for b in branches):
                return True
            for i, a in enumerate(branches):
                for j, b in enumerate(branches):
                    if i != j and (a.startswith(b) or b.startswith(a)):
                        return True
        return False

    def _check_redos_call(self, node: ast.Call) -> List[SecurityIssue]:
        if not isinstance(node.func, ast.Attribute):
            return []
        if not (isinstance(node.func.value, ast.Name) and node.func.value.id == "re"):
            return []
        if node.func.attr not in {"compile", "match", "search", "findall", "finditer", "sub", "split"}:
            return []
        if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
            return []

        pattern = node.args[0].value
        if self._has_nested_quantifier(pattern):
            return [SecurityIssue(
                HIGH, node.lineno, "redos",
                f"Regex with nested quantifiers '{pattern[:50]}' — vulnerable to ReDoS."
            )]
        if self._has_overlapping_alternation(pattern):
            return [SecurityIssue(
                MEDIUM, node.lineno, "redos",
                f"Regex with overlapping alternation and quantifier '{pattern[:50]}' — potential ReDoS risk."
            )]
        return []

    def _check_path_traversal_call(self, node: ast.Call) -> List[SecurityIssue]:
        if isinstance(node.func, ast.Name) and node.func.id == "open" and node.args:
            arg = node.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "../" in arg.value:
                return [SecurityIssue(MEDIUM, node.lineno, "path_traversal", "Path traversal via '../' in open().")]
            if isinstance(arg, ast.JoinedStr):
                raw = "".join(v.value for v in arg.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
                if "../" in raw:
                    return [SecurityIssue(MEDIUM, node.lineno, "path_traversal", "Path traversal via '../' in open().")]
        return []
