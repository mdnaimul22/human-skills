import ast
import io
import tokenize
from default.base import BaseRule, FileContext


class SectionCommentsRule(BaseRule):
    PRAGMA_PREFIXES = ("noqa", "type:", "pylint:", "pragma:", "fmt:", "isort:", "ruff:")
    MIN_INIT_MODULES = 2
    MIN_INIT_EXPORTS = 6
    MIN_SETTINGS_FIELDS = 8
    MAX_SETTINGS_BLOCK_SIZE = 10

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._comments: dict[int, str] = {}

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        if self.ctx.is_test_file:
            return [], []
        is_init = self.ctx.filename.name == "__init__.py"
        is_settings = self.ctx.is_settings_file or self.ctx.filename.name == "settings.py"
        if not is_init and not is_settings:
            return [], []

        self._comments = self._extract_comment_lines(self.ctx.content)
        if is_init:
            self._check_init_file(tree)
        if is_settings:
            self._check_settings_file(tree)
        return self.violations, self.advisories

    def _extract_comment_lines(self, content: str) -> dict[int, str]:
        comments: dict[int, str] = {}
        try:
            for tok in tokenize.generate_tokens(io.StringIO(content).readline):
                if tok.type == tokenize.COMMENT:
                    text = tok.string.lstrip("#").strip()
                    if text and not text.lower().startswith(self.PRAGMA_PREFIXES):
                        comments[tok.start[0]] = text
        except tokenize.TokenError:
            pass
        return comments

    def _has_comment_in_range(self, start_line: int, end_line: int) -> bool:
        return any(start_line <= ln <= end_line for ln in self._comments)

    def _check_init_file(self, tree: ast.AST) -> None:
        if not isinstance(tree, ast.Module):
            return

        symbol_to_mod: dict[str, str] = {}
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.level > 0 and node.module:
                for alias in node.names:
                    symbol_to_mod[alias.asname or alias.name] = f".{node.module}"

        for node in tree.body:
            if isinstance(node, ast.Assign):
                target_name = node.targets[0].id if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) else ""
                self._check_init_assignment(target_name, node.value, node.lineno, symbol_to_mod)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                self._check_init_assignment(node.target.id, node.value, node.lineno, symbol_to_mod)

    def _check_init_assignment(
        self, name: str, value: ast.expr, lineno: int, symbol_to_mod: dict[str, str]
    ) -> None:
        if isinstance(value, ast.Dict):
            self._check_lazy_export_dict(name, value, lineno)
        elif name == "__all__" and isinstance(value, (ast.List, ast.Tuple)):
            self._check_dunder_all(value, lineno, symbol_to_mod)

    def _check_lazy_export_dict(self, name: str, dict_node: ast.Dict, lineno: int) -> None:
        entries: list[tuple[int, int, str]] = []
        for k, v in zip(dict_node.keys, dict_node.values):
            if k is None:
                continue
            if isinstance(k, ast.Constant) and isinstance(k.value, str):
                if isinstance(v, ast.Constant) and isinstance(v.value, str) and v.value.startswith("."):
                    entries.append((k.lineno, v.end_lineno or v.lineno, v.value))

        unique_mods = dict.fromkeys(mod for _, _, mod in entries)
        if len(unique_mods) < self.MIN_INIT_MODULES or len(entries) <= self.MIN_INIT_EXPORTS:
            return

        missing_groups: list[str] = []
        prev_mod: str | None = None
        prev_end = dict_node.lineno
        for start_ln, end_ln, mod in entries:
            if mod != prev_mod:
                if not self._has_comment_in_range(prev_end, start_ln):
                    missing_groups.append(f"{mod} (L{start_ln})")
                prev_mod = mod
            prev_end = end_ln + 1

        if missing_groups:
            preview = ", ".join(missing_groups[:5])
            extra = f" (+{len(missing_groups) - 5} more)" if len(missing_groups) > 5 else ""
            label = name or "export map"
            self.add_violation(
                lineno,
                f"⚠️ [Readability Violation] '{label}' exports {len(entries)} symbols from {len(unique_mods)} files without '#' section headers: {preview}{extra}.",
                suggestion="Add a '# <module>.py' comment above each source-file group inside the export dictionary."
            )

    def _check_dunder_all(
        self, seq_node: ast.List | ast.Tuple, lineno: int, symbol_to_mod: dict[str, str]
    ) -> None:
        elts = [e for e in seq_node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        if len(elts) <= self.MIN_INIT_EXPORTS:
            return

        mods_used = {symbol_to_mod[e.value] for e in elts if e.value in symbol_to_mod}
        if len(mods_used) < self.MIN_INIT_MODULES:
            return

        end_ln = seq_node.end_lineno or lineno
        comment_count = sum(1 for ln in self._comments if lineno <= ln <= end_ln)
        if comment_count < len(mods_used):
            mod_list = ", ".join(sorted(mods_used)[:5])
            self.add_violation(
                lineno,
                f"⚠️ [Readability Violation] '__all__' lists {len(elts)} exports from {len(mods_used)} modules ({mod_list}) with only {comment_count} '#' section comment(s).",
                suggestion="Group '__all__' entries by source file and add '# <module>.py' comments above each section."
            )

    def _is_settings_class(self, node: ast.ClassDef) -> bool:
        if node.name == "Settings":
            return True
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BaseSettings":
                return True
            if isinstance(base, ast.Attribute) and base.attr == "BaseSettings":
                return True
        return False

    def _check_settings_file(self, tree: ast.AST) -> None:
        if not isinstance(tree, ast.Module):
            return

        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or not self._is_settings_class(node):
                continue

            fields: list[ast.stmt] = []
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    if not stmt.target.id.startswith("_") and stmt.target.id != "model_config":
                        fields.append(stmt)
                elif isinstance(stmt, ast.Assign) and len(stmt.targets) == 1 and isinstance(stmt.targets[0], ast.Name):
                    name = stmt.targets[0].id
                    if name.isupper() and not name.startswith("_"):
                        fields.append(stmt)

            if len(fields) <= self.MIN_SETTINGS_FIELDS:
                continue

            blocks: list[list[ast.stmt]] = [[fields[0]]]
            for prev_f, curr_f in zip(fields, fields[1:]):
                prev_end = prev_f.end_lineno or prev_f.lineno
                if curr_f.lineno - prev_end > 1:
                    blocks.append([curr_f])
                else:
                    blocks[-1].append(curr_f)

            first_ln = node.lineno
            last_ln = fields[-1].end_lineno or fields[-1].lineno
            total_headers = sum(1 for ln in self._comments if first_ln <= ln <= last_ln)

            if total_headers == 0:
                self.add_violation(
                    node,
                    f"⚠️ [Readability Violation] '{node.name}' defines {len(fields)} settings across {len(blocks)} group(s) with no '#' section headers.",
                    suggestion="Separate logical setting groups with clear '# Section Name' comments (e.g. '# Core & API', '# Database', '# Auth')."
                )
                continue

            prev_block_end = node.lineno
            for block in blocks:
                block_start = block[0].lineno
                block_end = block[-1].end_lineno or block[-1].lineno
                if not self._has_comment_in_range(prev_block_end + 1, block_start):
                    self.add_violation(
                        block[0],
                        f"⚠️ [Readability Violation] Settings group starting at L{block_start} ({len(block)} fields) is missing a '#' section header.",
                        suggestion="Add a '# Section Name' comment directly above this settings group."
                    )
                if len(block) > self.MAX_SETTINGS_BLOCK_SIZE:
                    self.add_violation(
                        block[0],
                        f"⚠️ [Readability Violation] Settings group at L{block_start} has {len(block)} unbroken fields (max {self.MAX_SETTINGS_BLOCK_SIZE} per section).",
                        suggestion="Split large settings blocks into smaller logical sections with '#' comments."
                    )
                prev_block_end = block_end
