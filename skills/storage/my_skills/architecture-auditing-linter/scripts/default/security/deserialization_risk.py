import ast
from typing import List

from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH


# suggestions per module
_FIX_HINTS = {
    'pickle':     "Use json or a safe serialization format instead.",
    'cPickle':    "Use json or a safe serialization format instead.",
    'yaml':       "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader).",
    'marshal':    "Avoid if possible, or validate input strictly.",
    'shelve':     "shelve uses pickle internally — avoid with untrusted data.",
    'jsonpickle': "Use json.loads() with a strict schema validator instead.",
    'dill':       "dill can execute arbitrary code — avoid with untrusted data.",
}


class DeserializationDetector(SecurityDetector):
    """Detects unsafe deserialization patterns via AST analysis."""

    name = "deserialization"
    description = "Detects pickle, yaml, marshal, shelve, jsonpickle, and dill deserialization risks."

    # (module, function) → severity
    # yaml.load is handled separately (SafeLoader check), but listed here for reference.
    UNSAFE_DESER = {
        ('pickle',     'load'):      CRITICAL,
        ('pickle',     'loads'):     CRITICAL,
        ('pickle',     'Unpickler'): CRITICAL,
        ('cPickle',    'load'):      CRITICAL,
        ('cPickle',    'loads'):     CRITICAL,
        ('marshal',    'loads'):     HIGH,
        ('marshal',    'load'):      HIGH,
        ('shelve',     'open'):      HIGH,
        ('jsonpickle', 'decode'):    CRITICAL,
        ('dill',       'load'):      CRITICAL,
        ('dill',       'loads'):     CRITICAL,
        # yaml.unsafe_load is always unsafe — no redemption path
        ('yaml',       'unsafe_load'): CRITICAL,
    }

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name):
                continue

            mod  = node.func.value.id
            func = node.func.attr
            pair = (mod, func)

            # yaml.load needs special handling — safe if SafeLoader is passed
            if pair == ('yaml', 'load'):
                issues.extend(self._check_yaml_load(node))
                continue

            # All other unsafe deserializers
            if pair in self.UNSAFE_DESER:
                sev  = self.UNSAFE_DESER[pair]
                fix  = _FIX_HINTS.get(mod, "Avoid if possible, or validate input strictly.")
                issues.append(SecurityIssue(
                    sev, node.lineno, "unsafe_deserialization",
                    f"'{mod}.{func}()' — unsafe deserialization allows arbitrary code execution. {fix}"
                ))

        return issues

    # ──────────────────────────────────────────────
    # Helper
    # ──────────────────────────────────────────────

    def _check_yaml_load(self, node: ast.Call) -> List[SecurityIssue]:
        """
        yaml.load() is safe only when Loader=yaml.SafeLoader (or FullLoader for non-exec).
        Flag it if no Loader kwarg, or if the Loader is not a Safe variant.
        """
        has_safe_loader = any(
            kw.arg == 'Loader' and (
                (isinstance(kw.value, ast.Attribute) and 'Safe' in kw.value.attr) or
                (isinstance(kw.value, ast.Name)      and 'Safe' in kw.value.id)
            )
            for kw in node.keywords
        )

        if not has_safe_loader:
            return [SecurityIssue(
                CRITICAL, node.lineno, "unsafe_deserialization",
                "'yaml.load()' without SafeLoader — allows arbitrary code execution. "
                "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)."
            )]

        return []