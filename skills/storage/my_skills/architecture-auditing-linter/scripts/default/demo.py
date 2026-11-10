import ast
import logging
from typing import Any, Dict, List, Optional, Set, Tuple


class UDBDPlugin:
    def __init__(self):
        self.logger = logging.getLogger('UDBDPlugin')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.logger.propagate = False

    def analyze_source(self, src: str, source_name: str = "source") -> Dict[str, Any]:
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            self.logger.error(f"{source_name} has syntax error: {e}")
            return {"error": str(e), "unused_methods": []}
        return self._detect_unused_methods(tree, source_name=source_name)

    def analyze_tree(self, tree: ast.AST, source_name: str = "source") -> Dict[str, Any]:
        return self._detect_unused_methods(tree, source_name=source_name)

    def _detect_unused_methods(self, tree: ast.AST, candidate: Any = None, source_name: str = "source") -> Dict[str, Any]:
        method_analyzer = MethodAnalyzer()
        method_analyzer.analyze(tree)
        
        unused_methods = []
        
        for method_key, method_info in method_analyzer.all_methods.items():
            class_name, method_name = method_key
            
            if (method_name.startswith('__') and method_name.endswith('__')) or not method_name.startswith('_'):
                continue
            
            is_used = self._is_method_used_enhanced(
                class_name, method_name, method_analyzer
            )
            
            if not is_used:
                unused_methods.append({
                    'class_name': class_name,
                    'method_name': method_name,
                    'line_number': method_info['line_number'],
                    'full_signature': f"{class_name}.{method_name}()"
                })
        
        candidate_key = getattr(candidate, "key", lambda: source_name)() if candidate else source_name
        return {
            'unused_methods': unused_methods,
            'all_methods': method_analyzer.all_methods,
            'all_calls': method_analyzer.get_all_calls(),
            'local_function_calls': method_analyzer.local_function_calls,
            'debug_info': method_analyzer.get_debug_info(),
            'candidate_key': candidate_key
        }

    def _is_method_used_enhanced(self, class_name: str, method_name: str, 
                                analyzer: 'MethodAnalyzer') -> bool:
        if (class_name, method_name) in analyzer.local_method_calls:
            return True
        
        if method_name in analyzer.local_function_calls.get(class_name, set()):
            return True
        
        if (class_name, method_name) in analyzer.self_method_calls:
            return True
        
        if (class_name, method_name) in analyzer.instance_method_calls:
            return True
        
        if (class_name, method_name) in analyzer.static_style_calls:
            return True
        
        if method_name in analyzer.method_names_called:
            return True
        
        if method_name in analyzer.attribute_references:
            return True
        
        if method_name in analyzer.string_method_references:
            return True
        
        if method_name in analyzer.dynamic_calls:
            return True
        
        return False

    def _log_detailed_unused_info(self, methods_info: Dict, candidate_key: str = "source"):
        self.logger.warning(f"UNUSED DEPENDENCIES: {len(methods_info['unused_methods'])} methods in {candidate_key}")
        
        if methods_info['unused_methods']:
            self.logger.debug(f"UNUSED METHODS ({len(methods_info['unused_methods'])} found):")
            for i, method_info in enumerate(methods_info['unused_methods'], 1):
                full_sig = method_info['full_signature']
                line_num = method_info['line_number']
                self.logger.debug(f"  {i}. Line {line_num}: {full_sig}")
        
        if methods_info['unused_methods'] or self.logger.level <= logging.DEBUG:
            debug_info = methods_info.get('debug_info', {})
            self.logger.debug(f"ENHANCED DEBUG INFO:")
            self.logger.debug(f"  Total methods found: {len(methods_info['all_methods'])}")
            self.logger.debug(f"  Total calls found: {len(methods_info['all_calls'])}")
            self.logger.debug(f"  Local function calls: {len(methods_info.get('local_function_calls', {}))}")
            
            local_calls = methods_info.get('local_function_calls', {})
            for class_name, calls in local_calls.items():
                if calls:
                    self.logger.debug(f"  Local calls in {class_name}: {list(calls)}")
            
            example_calls = list(methods_info['all_calls'])[:8]
            if example_calls:
                self.logger.debug(f"  Example calls detected: {example_calls}")
        
        total_issues = len(methods_info['unused_methods'])
        self.logger.warning(f"SUMMARY: {total_issues} unused method(s)")


class MethodAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.all_methods = {}
        self.current_class = None
        self.current_method = None
        
        self.local_method_calls = set()
        self.local_function_calls = {}
        self.self_method_calls = set()
        self.instance_method_calls = set()
        self.static_style_calls = set()
        self.method_names_called = set()
        self.attribute_references = set()
        self.string_method_references = set()
        self.dynamic_calls = set()
        
        self.class_stack = []
        self.method_stack = []

    def analyze(self, tree: ast.AST):
        self.visit(tree)
        
    def get_all_calls(self) -> set:
        all_calls = set()
        all_calls.update(f"{cls}.{method}" for cls, method in self.local_method_calls)
        all_calls.update(f"self.{method}" for cls, method in self.self_method_calls)
        all_calls.update(f"{cls}().{method}" for cls, method in self.static_style_calls)
        all_calls.update(f"local_{method}" for method_set in self.local_function_calls.values() for method in method_set)
        all_calls.update(f"attr_{attr}" for attr in self.attribute_references)
        return all_calls
    
    def get_debug_info(self) -> Dict[str, Any]:
        return {
            'local_method_calls': len(self.local_method_calls),
            'local_function_calls': {k: len(v) for k, v in self.local_function_calls.items()},
            'self_method_calls': len(self.self_method_calls),
            'instance_method_calls': len(self.instance_method_calls),
            'static_style_calls': len(self.static_style_calls),
            'method_names_called': len(self.method_names_called),
            'attribute_references': len(self.attribute_references),
            'string_method_references': len(self.string_method_references),
            'dynamic_calls': len(self.dynamic_calls)
        }

    def visit_ClassDef(self, node):
        self.class_stack.append(node.name)
        self.current_class = node.name
        
        if self.current_class not in self.local_function_calls:
            self.local_function_calls[self.current_class] = set()
        
        self.generic_visit(node)
        
        self.class_stack.pop()
        self.current_class = self.class_stack[-1] if self.class_stack else None

    def visit_FunctionDef(self, node):
        if self.current_class:
            method_key = (self.current_class, node.name)
            self.all_methods[method_key] = {
                'line_number': node.lineno,
                'node': node,
                'class_name': self.current_class
            }
        
        self.method_stack.append((self.current_class, node.name))
        old_method = self.current_method
        self.current_method = node.name
        
        self.generic_visit(node)
        
        self.method_stack.pop()
        self.current_method = old_method

    def visit_AsyncFunctionDef(self, node):
        if self.current_class:
            method_key = (self.current_class, node.name)
            self.all_methods[method_key] = {
                'line_number': node.lineno,
                'node': node,
                'class_name': self.current_class
            }
        
        self.method_stack.append((self.current_class, node.name))
        old_method = self.current_method
        self.current_method = node.name
        
        self.generic_visit(node)
        
        self.method_stack.pop()
        self.current_method = old_method

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            self.method_names_called.add(method_name)
            
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
                if self.current_class:
                    self.self_method_calls.add((self.current_class, method_name))
                    self.local_method_calls.add((self.current_class, method_name))
            
            elif isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                if self.current_class and obj_name.lower() == self.current_class.lower():
                    self.instance_method_calls.add((self.current_class, method_name))
            
            elif isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    class_name = node.func.value.func.id
                    self.static_style_calls.add((class_name, method_name))
                    if class_name == self.current_class:
                        self.local_method_calls.add((class_name, method_name))

        elif isinstance(node.func, ast.Name):
            function_name = node.func.id
            if self.current_class:
                method_key = (self.current_class, function_name)
                if method_key in self.all_methods or function_name.startswith('_'):
                    self.local_function_calls[self.current_class].add(function_name)
                    self.local_method_calls.add((self.current_class, function_name))

        self.generic_visit(node)

    def visit_Attribute(self, node):
        if hasattr(node, 'attr'):
            self.attribute_references.add(node.attr)
            
            if isinstance(node.value, ast.Name) and node.value.id == 'self' and self.current_class:
                if node.attr.startswith('_'):
                    self.local_method_calls.add((self.current_class, node.attr))
                    
        self.generic_visit(node)

    def visit_Str(self, node):
        if hasattr(node, 's') and isinstance(node.s, str):
            if node.s.startswith('_') and node.s.replace('_', '').isalnum():
                self.string_method_references.add(node.s)
                self.dynamic_calls.add(node.s)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            if node.value.startswith('_') and node.value.replace('_', '').isalnum():
                self.string_method_references.add(node.value)
                self.dynamic_calls.add(node.value)
        self.generic_visit(node)


try:
    from default.base import BaseRule, FileContext
except ImportError:
    BaseRule = None
    FileContext = None

if BaseRule is not None:
    class UDBDMethodRule(BaseRule):
        def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
            if self.ctx.is_test_file:
                return self.violations, self.advisories
            detector = UDBDPlugin()
            info = detector.analyze_tree(tree, source_name=str(self.ctx.rel_path))
            for m in info.get("unused_methods", []):
                self.add_violation(
                    m["line_number"],
                    f"❌ [Dead Code Violation] Private method '{m['full_signature']}' is defined but never called or referenced.",
                    suggestion=f"Remove '{m['method_name']}' or invoke it where required."
                )
            return self.violations, self.advisories


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        with open(target, "r", encoding="utf-8") as f:
            src_code = f.read()
        detector = UDBDPlugin()
        res = detector.analyze_source(src_code, source_name=target)
        detector._log_detailed_unused_info(res, candidate_key=target)
        print(f"Total unused methods: {len(res['unused_methods'])}")
        for item in res["unused_methods"]:
            print(f"  L{item['line_number']}: {item['full_signature']}")



try:
    from default.base import BaseRule, FileContext
except ImportError:
    BaseRule = None
    FileContext = None

if BaseRule is not None:
    class UDBDMethodRule(BaseRule):
        def run(self, tree: ast.AST) -> tuple[list[str], list[str]]:
            if self.ctx.is_test_file:
                return self.violations, self.advisories
            detector = UDBDPlugin()
            info = detector.analyze_tree(tree, source_name=str(self.ctx.rel_path))
            for m in info.get("unused_methods", []):
                self.add_violation(
                    m["line_number"],
                    f"❌ [Dead Code Violation] Private method '{m['full_signature']}' is defined but never called or referenced.",
                    suggestion=f"Remove '{m['method_name']}' or invoke it where required."
                )
            return self.violations, self.advisories


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        target = sys.argv[1]
        with open(target, "r", encoding="utf-8") as f:
            src_code = f.read()
        detector = UDBDPlugin()
        res = detector.analyze_source(src_code, source_name=target)
        detector._log_detailed_unused_info(res, candidate_key=target)
        print(f"Total unused methods: {len(res['unused_methods'])}")
        for item in res["unused_methods"]:
            print(f"  L{item['line_number']}: {item['full_signature']}")