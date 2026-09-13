import ast
import importlib.util
from pathlib import Path
from default.base import BaseRule
from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH, MEDIUM, LOW


class SecurityRule(BaseRule):
    def __init__(self, context):
        super().__init__(context)
        self._detectors = self._load_detectors()

    def _load_detectors(self) -> list[SecurityDetector]:
        detectors = []
        sec_dir = Path(__file__).resolve().parent / "security"
        if not sec_dir.exists():
            return detectors

        for py_file in sorted(sec_dir.glob("*_risk.py")):
            module_name = f"default.security.{py_file.stem}"
            spec = importlib.util.spec_from_file_location(module_name, py_file)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            for attr in vars(mod).values():
                if isinstance(attr, type) and issubclass(attr, SecurityDetector) and attr is not SecurityDetector:
                    detectors.append(attr())
        return detectors

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        content = self.ctx.content
        severity_icons = {
            CRITICAL: "🚨",
            HIGH: "❌",
            MEDIUM: "⚠️",
            LOW: "ℹ️"
        }

        has_critical = False
        seen_issues = set()

        for detector in self._detectors:
            try:
                issues = detector.detect(tree, content)
                for issue in issues:
                    key = (issue.line, issue.category, issue.message)
                    if key in seen_issues:
                        continue
                    seen_issues.add(key)

                    if issue.severity == CRITICAL:
                        has_critical = True

                    icon = severity_icons.get(issue.severity, "⚠️")
                    cat_label = issue.category.replace("_", " ").title()
                    msg = f"{icon} [Security: {cat_label}] ({issue.severity}) {issue.message}"
                    self.add_violation(issue.line, msg)
            except Exception:
                continue

        if has_critical:
            self.add_advisory(
                "🚨 [Critical Security Advisory] High-severity vulnerabilities detected. "
                "Audit database queries, command execution, and cryptographic keys before production deployment."
            )

        return self.violations, self.advisories
