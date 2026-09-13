import ast
import re
from typing import List, Set

from default.security import SecurityDetector, SecurityIssue, HIGH, MEDIUM, LOW


# Modules known to use extractall/extract for archive operations
_ARCHIVE_MODULES = {'zipfile', 'tarfile', 'ZipFile', 'TarFile'}

# Variable name hints that suggest archive objects
_ARCHIVE_NAME_HINTS = {'zip', 'tar', 'archive', 'zf', 'tf', 'z', 'arc'}


class ResourceDetector(SecurityDetector):
    """Detects ReDoS, zip bombs, symlink attacks, and memory issues."""

    name = "resource"
    description = "Detects ReDoS, zip bomb/slip, symlink attacks, unbounded read, and path traversal."

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []

        # Build a set of variable names assigned from archive opens
        # e.g. with zipfile.ZipFile(...) as zf → zf is archive
        archive_vars: Set[str] = self._collect_archive_vars(tree)

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                issues.extend(self._check_call(node, archive_vars))

        # Regex-based detections
        issues.extend(self._detect_redos(source_code))
        issues.extend(self._detect_path_traversal(source_code))

        return issues

    # ──────────────────────────────────────────────
    # Archive variable collection
    # ──────────────────────────────────────────────

    def _collect_archive_vars(self, tree: ast.AST) -> Set[str]:
        """
        Collect variable names that are assigned from archive open calls.

        Handles:
            with zipfile.ZipFile(...) as zf         → zf
            with tarfile.open(...) as tf             → tf
            zf = zipfile.ZipFile(...)               → zf
            zf = ZipFile(...)                        → zf
        """
        archive_vars: Set[str] = set()

        for node in ast.walk(tree):
            # with ... as var:
            if isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars and isinstance(item.optional_vars, ast.Name):
                        if self._is_archive_call(item.context_expr):
                            archive_vars.add(item.optional_vars.id)

            # var = zipfile.ZipFile(...) or var = ZipFile(...)
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        if self._is_archive_call(node.value):
                            archive_vars.add(target.id)

        return archive_vars

    def _is_archive_call(self, node: ast.expr) -> bool:
        """Return True if the node is a call to an archive open function."""
        if not isinstance(node, ast.Call):
            return False

        # zipfile.ZipFile(...) / tarfile.open(...)
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                if node.func.value.id in _ARCHIVE_MODULES:
                    return True
            if node.func.attr in ('ZipFile', 'open') and isinstance(node.func.value, ast.Name):
                if node.func.value.id in _ARCHIVE_MODULES:
                    return True

        # ZipFile(...) / TarFile(...)
        if isinstance(node.func, ast.Name):
            if node.func.id in _ARCHIVE_MODULES:
                return True

        return False

    # ──────────────────────────────────────────────
    # Call checks
    # ──────────────────────────────────────────────

    def _check_call(self, node: ast.Call, archive_vars: Set[str]) -> List[SecurityIssue]:
        results = []

        if not isinstance(node.func, ast.Attribute):
            return results

        func = node.func.attr
        caller_name = self._get_caller_name(node)

        # ── extractall() — zip bomb ──
        if func == 'extractall':
            if self._is_archive_context(node, caller_name, archive_vars):
                # Check if a members/filter argument is passed (size-safe extraction)
                has_filter = any(
                    kw.arg in ('members', 'filter') for kw in node.keywords
                ) or len(node.args) > 1
                if not has_filter:
                    results.append(SecurityIssue(
                        MEDIUM, node.lineno, "zip_bomb",
                        f"'{caller_name}.extractall()' without size validation — "
                        "vulnerable to zip bombs. Pass a 'members' generator that checks sizes."
                    ))

        # ── extract() — zip slip ──
        if func == 'extract':
            if self._is_archive_context(node, caller_name, archive_vars):
                # Check if destination path is validated (second arg or path= kwarg)
                has_path_check = any(kw.arg == 'path' for kw in node.keywords)
                results.append(SecurityIssue(
                    LOW, node.lineno, "zip_slip",
                    f"'{caller_name}.extract()' — verify extracted paths don't escape "
                    "the target directory (zip slip attack)."
                    + (" Consider using extractall() with a members filter." if not has_path_check else "")
                ))

        # ── os.symlink ──
        if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and func == 'symlink':
            results.append(SecurityIssue(
                MEDIUM, node.lineno, "symlink_attack",
                "'os.symlink()' — symlinks can be exploited to access unauthorized files."
            ))

        # ── .read() without size limit ──
        if func == 'read' and not node.args:
            results.append(SecurityIssue(
                LOW, node.lineno, "unbounded_read",
                "'.read()' without size limit — may cause memory exhaustion with large data."
            ))

        return results

    def _is_archive_context(self, node: ast.Call, caller_name: str, archive_vars: Set[str]) -> bool:
        """
        Return True if this extractall/extract call is on an archive object.

        Checks:
            1. Caller variable is in our collected archive_vars set
            2. Caller name has archive-related hints (zip, tar, zf, tf, etc.)
            3. Caller is a direct archive module attribute (zipfile.ZipFile)
        """
        if caller_name in archive_vars:
            return True

        # Name hints: zf, zip_ref, tar_obj, archive, etc.
        caller_lower = caller_name.lower()
        if any(hint in caller_lower for hint in _ARCHIVE_NAME_HINTS):
            return True

        # Direct call: zipfile.ZipFile(...).extractall()
        if isinstance(node.func.value, ast.Call):
            if self._is_archive_call(node.func.value):
                return True

        return False

    def _get_caller_name(self, node: ast.Call) -> str:
        """Extract caller name string from a Call node's func attribute."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id
            if isinstance(node.func.value, ast.Attribute):
                return node.func.value.attr
        return "unknown"

    # ──────────────────────────────────────────────
    # ReDoS detection
    # ──────────────────────────────────────────────

    def _detect_redos(self, source_code: str) -> List[SecurityIssue]:
        """Detect ReDoS-vulnerable regex patterns."""
        issues = []
        regex_funcs = r're\.(?:compile|match|search|findall|finditer|sub|split)\s*\(\s*[rf]?["\']([^"\']+)["\']'

        for match in re.finditer(regex_funcs, source_code):
            pattern = match.group(1)
            line = source_code[:match.start()].count('\n') + 1

            # Nested quantifiers: (a+)+, (a*)+, (.+)*, etc.
            if re.search(r'\([^)]*[+*]\)\s*[+*]', pattern):
                issues.append(SecurityIssue(
                    HIGH, line, "redos",
                    f"Regex with nested quantifiers '{pattern[:50]}' — vulnerable to ReDoS."
                ))

            # Overlapping alternation with quantifiers: (a|a)+
            elif re.search(r'\([^)]*\|[^)]*\)\s*[+*]', pattern):
                issues.append(SecurityIssue(
                    MEDIUM, line, "redos",
                    f"Regex with alternation and quantifier '{pattern[:50]}' — potential ReDoS risk."
                ))

        return issues

    # ──────────────────────────────────────────────
    # Path traversal detection
    # ──────────────────────────────────────────────

    def _detect_path_traversal(self, source_code: str) -> List[SecurityIssue]:
        """Detect path traversal patterns."""
        issues = []
        patterns = [
            (r'open\s*\([^)]*\.\./', MEDIUM, "Path traversal via '../' in open()."),
            (r'os\.path\.join\s*\([^)]*\+', LOW, "Potentially unsafe os.path.join with concatenation."),
        ]
        for pattern, severity, message in patterns:
            for match in re.finditer(pattern, source_code):
                line = source_code[:match.start()].count('\n') + 1
                issues.append(SecurityIssue(severity, line, "path_traversal", message))

        return issues