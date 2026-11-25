import ast
from default.base import BaseRule, FileContext


class TypeSafetyRule(BaseRule):
    EQUALITY_DUNDERS = {"__eq__", "__ne__"}
    BEFORE_VALIDATORS = {"field_validator", "model_validator", "validator", "root_validator"}

    def __init__(self, context: FileContext):
        super().__init__(context)
        self._in_equality_dunder = 0
        self._in_before_validator = 0
        self._typing_cast_imported = False
        self._non_typing_cast_imported = False

    def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    bound = alias.asname or alias.name
                    if bound == "cast":
                        if node.module in ("typing", "typing_extensions"):
                            self._typing_cast_imported = True
                        else:
                            self._non_typing_cast_imported = True
        return super().run(tree)

    @staticmethod
    def _contains_any_type(node: ast.AST | None) -> bool:
        if not node:
            return False
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id == "Any":
                return True
            if isinstance(child, ast.Attribute) and child.attr == "Any":
                if isinstance(child.value, ast.Name) and child.value.id == "typing":
                    return True
        return False

    @staticmethod
    def _contains_object_type(node: ast.AST | None) -> bool:
        if not node:
            return False
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id == "object":
                return True
            if isinstance(child, ast.Attribute) and child.attr == "object":
                if isinstance(child.value, ast.Name) and child.value.id == "builtins":
                    return True
        return False

    def _is_before_validator(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            dec_name = dec.func.id if isinstance(dec.func, ast.Name) else (
                dec.func.attr if isinstance(dec.func, ast.Attribute) else ""
            )
            if dec_name not in self.BEFORE_VALIDATORS:
                continue
            for kw in dec.keywords:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and kw.value.value == "before":
                    return True
                if kw.arg == "pre" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    return True
        return False

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "typing.Any":
                self.add_violation(
                    node,
                    "❌ [Type Safety Violation] 'typing.Any' imported.",
                    suggestion="Using 'Any' disables Mypy/Pyright type checking. Replace with concrete types, Pydantic models, or TypeVar."
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "typing":
            for alias in node.names:
                if alias.name == "Any":
                    self.add_violation(
                        node,
                        "❌ [Type Safety Violation] Direct 'from typing import Any' import detected.",
                        suggestion="Using 'Any' completely disables static type checking. Replace with concrete types, Pydantic models, TypedDict, or Generic TypeVar[T]."
                    )
        self.generic_visit(node)

    def _check_func_annotations(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        is_eq = node.name in self.EQUALITY_DUNDERS

        if node.returns:
            if self._contains_any_type(node.returns):
                ret_str = ast.unparse(node.returns)
                self.add_violation(
                    node,
                    f"❌ [Type Safety Violation] Function '{node.name}' has return type containing 'Any' ('{ret_str}').",
                    suggestion=f"Specify a concrete return type (e.g. 'ResponsePayload', 'dict[str, str]', 'None') instead of '{ret_str}'."
                )
            elif self._contains_object_type(node.returns):
                ret_str = ast.unparse(node.returns)
                self.add_violation(
                    node,
                    f"❌ [Type Safety Violation] Function '{node.name}' has untyped root 'object' in return annotation ('{ret_str}').",
                    suggestion=f"Using 'object' is a lazy escape hatch that completely destroys static typing. Return a concrete Pydantic BaseModel, TypedDict, or domain entity instead of '{ret_str}'."
                )

        for arg in node.args.args + node.args.kwonlyargs:
            if arg.annotation:
                if self._contains_any_type(arg.annotation):
                    arg_ann_str = ast.unparse(arg.annotation)
                    self.add_violation(
                        arg,
                        f"❌ [Type Safety Violation] Parameter '{arg.arg}' in function '{node.name}' annotated with 'Any' ('{arg_ann_str}').",
                        suggestion=f"Define a concrete Pydantic schema or TypedDict for parameter '{arg.arg}' instead of '{arg_ann_str}'."
                    )
                elif self._contains_object_type(arg.annotation) and not is_eq:
                    arg_ann_str = ast.unparse(arg.annotation)
                    self.add_violation(
                        arg,
                        f"❌ [Type Safety Violation] Parameter '{arg.arg}' in function '{node.name}' annotated with root 'object' ('{arg_ann_str}').",
                        suggestion=f"Passing 'object' allows arbitrary invalid values to bypass validation. Enforce an explicit Pydantic schema, Protocol, or TypedDict for '{arg.arg}' instead of '{arg_ann_str}'."
                    )

    def _visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self._check_func_annotations(node)
        is_eq = node.name in self.EQUALITY_DUNDERS
        is_before = self._is_before_validator(node)
        if is_eq:
            self._in_equality_dunder += 1
        if is_before:
            self._in_before_validator += 1
        self.generic_visit(node)
        if is_eq:
            self._in_equality_dunder -= 1
        if is_before:
            self._in_before_validator -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self._contains_any_type(node.annotation):
            var_name = ast.unparse(node.target) if hasattr(node, "target") else "variable"
            ann_str = ast.unparse(node.annotation)
            suggestion = (
                f"Replace 'Any' in '{ann_str}' with an explicit domain model (e.g. Pydantic BaseModel), "
                f"a specific TypedDict, or bounded TypeVar. Never allow untyped boundaries."
            )
            self.add_violation(
                node,
                f"❌ [Type Safety Violation] Variable '{var_name}' annotated with 'Any' ('{ann_str}').",
                suggestion=suggestion
            )
        elif self._contains_object_type(node.annotation):
            var_name = ast.unparse(node.target) if hasattr(node, "target") else "variable"
            ann_str = ast.unparse(node.annotation)
            suggestion = (
                f"Using 'object' in '{ann_str}' is an evasion of domain modeling (Malicious Compliance). "
                f"Replace with an explicit Pydantic BaseModel, TypedDict, or Discriminated Union. Never use 'object' as a placeholder type."
            )
            self.add_violation(
                node,
                f"❌ [Type Safety Violation] Variable '{var_name}' annotated with root 'object' ('{ann_str}').",
                suggestion=suggestion
            )
        self.generic_visit(node)

    @staticmethod
    def _is_exception_type_expr(node: ast.AST) -> bool:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name) and (sub.id in ("BaseException", "Exception") or sub.id.endswith(("Error", "Exception"))):
                return True
            if isinstance(sub, ast.Attribute) and (sub.attr in ("BaseException", "Exception") or sub.attr.endswith(("Error", "Exception"))):
                return True
        return False

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id == "getattr":
            obj_repr = ast.unparse(node.args[0]) if len(node.args) >= 1 else "obj"
            attr_repr = ast.unparse(node.args[1]) if len(node.args) >= 2 else "'attr'"
            default_repr = f", {ast.unparse(node.args[2])}" if len(node.args) >= 3 else ""
            call_snippet = f"getattr({obj_repr}, {attr_repr}{default_repr})"

            clean_attr = attr_repr.strip("'\"")
            if attr_repr.startswith(("'", '"')):
                if default_repr:
                    def_val = ast.unparse(node.args[2])
                    suggestion = (
                        f"Avoid dynamic reflection. Define '{clean_attr}' in the schema or model: "
                        f"'{clean_attr}: <Type> | None = {def_val}'. Then access directly via '{obj_repr}.{clean_attr}'."
                    )
                else:
                    suggestion = f"Access attribute directly: '{obj_repr}.{clean_attr}'. Ensure '{clean_attr}' is defined on the class or Pydantic model."
            else:
                suggestion = (
                    f"Dynamic attribute/method dispatch detected ({attr_repr}). "
                    f"Replace with an explicit Strategy registry: 'REGISTRY: dict[KeyType, Callable] = {{...}}' "
                    f"and retrieve via 'REGISTRY.get({attr_repr})'."
                )

            self.add_violation(
                node,
                f"❌ [Type Safety Violation] Dynamic '{call_snippet}' used.",
                suggestion=suggestion
            )

        if isinstance(node.func, ast.Name) and node.func.id == "setattr":
            obj_repr = ast.unparse(node.args[0]) if len(node.args) >= 1 else "obj"
            attr_repr = ast.unparse(node.args[1]) if len(node.args) >= 2 else "'attr'"
            val_repr = ast.unparse(node.args[2]) if len(node.args) >= 3 else "val"
            clean_attr = attr_repr.strip("'\"")

            if attr_repr.startswith(("'", '"')):
                suggestion = f"Assign directly: '{obj_repr}.{clean_attr} = {val_repr}' or use Pydantic '{obj_repr}.model_copy(update={{{attr_repr}: {val_repr}}})'."
            else:
                suggestion = f"Avoid dynamic attribute mutation on '{obj_repr}'. Use a structured dictionary or Pydantic model."

            self.add_violation(
                node,
                f"❌ [Type Safety Violation] Dynamic 'setattr({obj_repr}, {attr_repr}, ...)' used.",
                suggestion=suggestion
            )

        if isinstance(node.func, ast.Name) and node.func.id == "hasattr":
            obj_repr = ast.unparse(node.args[0]) if len(node.args) >= 1 else "obj"
            attr_repr = ast.unparse(node.args[1]) if len(node.args) >= 2 else "'attr'"
            clean_attr = attr_repr.strip("'\"")
            suggestion = (
                f"Defensive attribute probing detected. Avoid 'hasattr()'. Enforce strict data contracts "
                f"using Pydantic models, TypedDict, or Protocols where '{clean_attr}' is guaranteed to exist."
            )
            self.add_violation(
                node,
                f"❌ [Type Safety Violation] Defensive 'hasattr({obj_repr}, {attr_repr})' used.",
                suggestion=suggestion
            )

        if isinstance(node.func, ast.Name) and node.func.id == "isinstance":
            is_ast_check = False
            is_object_check = False
            is_exc_check = False
            if len(node.args) >= 2:
                is_exc_check = self._is_exception_type_expr(node.args[1])
                for sub in ast.walk(node.args[1]):
                    if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "ast":
                        is_ast_check = True
                        break
                    if isinstance(sub, ast.Name) and sub.id == "AST":
                        is_ast_check = True
                        break
                    if isinstance(sub, ast.Name) and sub.id == "object":
                        is_object_check = True
                        break

            if is_object_check:
                obj_repr = ast.unparse(node.args[0]) if len(node.args) >= 1 else "val"
                type_repr = ast.unparse(node.args[1]) if len(node.args) >= 2 else "object"
                suggestion = (
                    f"Every value, class, and instance in Python inherits from 'object'. Checking 'isinstance({obj_repr}, {type_repr})' "
                    f"is a meaningless tautology that provides zero runtime guarantees or type narrowing. "
                    f"Enforce strict domain types at the boundary using Pydantic schemas or structural Protocols."
                )
                self.add_violation(
                    node,
                    f"❌ [Type Safety Violation] Meaningless tautological check 'isinstance({obj_repr}, {type_repr})' detected.",
                    suggestion=suggestion
                )
            elif not is_ast_check and not is_exc_check and self._in_equality_dunder == 0 and self._in_before_validator == 0:
                obj_repr = ast.unparse(node.args[0]) if len(node.args) >= 1 else "obj"
                type_repr = ast.unparse(node.args[1]) if len(node.args) >= 2 else "Type"
                suggestion = (
                    f"Type branching smell detected ('isinstance({obj_repr}, {type_repr})'). "
                    f"Replace type-checks with Polymorphism (Strategy Pattern / Protocol with unified methods), "
                    f"Pydantic Discriminated Unions, or Pattern Matching (match/case with assert_never)."
                )
                self.add_violation(
                    node,
                    f"❌ [Type Safety Violation] Type branching 'isinstance({obj_repr}, {type_repr})' used.",
                    suggestion=suggestion
                )

        if isinstance(node.func, ast.Name) and node.func.id == "cast":
            is_typing_cast = self._typing_cast_imported or not self._non_typing_cast_imported
            if is_typing_cast and len(node.args) >= 1 and self._contains_object_type(node.args[0]):
                type_repr = ast.unparse(node.args[0])
                suggestion = (
                    f"Casting to '{type_repr}' completely destroys static type safety. "
                    f"Cast to a concrete domain model, TypedDict, or Protocol instead."
                )
                self.add_violation(
                    node,
                    f"❌ [Type Safety Violation] Explicit cast to root '{type_repr}' detected.",
                    suggestion=suggestion
                )

        self.generic_visit(node)
