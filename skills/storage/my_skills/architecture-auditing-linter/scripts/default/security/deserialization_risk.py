import ast
from typing import List

from default.security import SecurityDetector, SecurityIssue, CRITICAL, HIGH


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
    name = "deserialization"
    description = "Detects pickle, yaml, marshal, shelve, jsonpickle, and dill deserialization risks."

    SAFE_YAML_LOADERS = {'SafeLoader', 'CSafeLoader', 'FullLoader', 'CFullLoader', 'BaseLoader', 'CBaseLoader'}

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
        ('yaml',       'unsafe_load'): CRITICAL,
    }

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        issues: List[SecurityIssue] = []
        uses_ruamel = self._uses_ruamel_yaml(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            if not isinstance(node.func.value, ast.Name):
                continue

            mod = node.func.value.id
            func = node.func.attr
            pair = (mod, func)

            if pair == ('yaml', 'load'):
                if not uses_ruamel:
                    issues.extend(self._check_yaml_load(node))
                continue

            if pair in self.UNSAFE_DESER:
                sev = self.UNSAFE_DESER[pair]
                fix = _FIX_HINTS.get(mod, "Avoid if possible, or validate input strictly.")
                issues.append(SecurityIssue(
                    sev, node.lineno, "unsafe_deserialization",
                    f"'{mod}.{func}()' — unsafe deserialization allows arbitrary code execution. {fix}"
                ))

        return issues

    @staticmethod
    def _uses_ruamel_yaml(tree: ast.AST) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("ruamel"):
                return True
            if isinstance(node, ast.Import) and any(a.name.startswith("ruamel") for a in node.names):
                return True
        return False

    def _is_safe_loader_node(self, node: ast.expr) -> bool:
        if isinstance(node, ast.Attribute) and node.attr in self.SAFE_YAML_LOADERS:
            return True
        if isinstance(node, ast.Name) and node.id in self.SAFE_YAML_LOADERS:
            return True
        return False

    def _check_yaml_load(self, node: ast.Call) -> List[SecurityIssue]:
        has_safe_loader = any(
            kw.arg == 'Loader' and self._is_safe_loader_node(kw.value)
            for kw in node.keywords
        )
        if not has_safe_loader and len(node.args) >= 2:
            has_safe_loader = self._is_safe_loader_node(node.args[1])

        if not has_safe_loader:
            return [SecurityIssue(
                CRITICAL, node.lineno, "unsafe_deserialization",
                "'yaml.load()' without SafeLoader — allows arbitrary code execution. "
                "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)."
            )]

        return []
