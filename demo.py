import ast
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

from core.plugin_manager import Plugin
from evo_lib.models import Candidate
from evo_lib.metrics import Metrics


class UDBDPlugin(Plugin):
    def __init__(self):
        # Set up detailed logging
        self.logger = logging.getLogger('UDBDPlugin')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        # Prevent duplicate logs via root logger
        self.logger.propagate = False

    def evaluate(self, population: List[Candidate]) -> Dict[str, Any]:
        recommendations = []
        for candidate in population:
            if candidate.metrics:
                continue

            try:
                tree = ast.parse(candidate.src)
            except SyntaxError as e:
                self.logger.error(f"Candidate {candidate.key()} has syntax error: {e}")
                candidate.veto(f"Syntax error: {e}")
                candidate.metrics = Metrics(scores={'fitness': float('-inf'), 'protection_veto': 1.0})
                recommendations.append(f"Rejected candidate {candidate.key()} for syntax error.")
                continue

            # Check for unused methods with enhanced detection
            unused_methods_info = self._detect_unused_methods(tree, candidate)
            
            # Calculate score based only on unused methods
            unused_methods_score = 1.0 if unused_methods_info['unused_methods'] else 0.0
            
            if unused_methods_score > 0.0:
                self._log_detailed_unused_info(candidate, unused_methods_info)
                
                # Use built-in veto method
                candidate.veto(
                    f"Unused dependencies: {len(unused_methods_info['unused_methods'])} methods"
                )
                
                # Set metrics with protection_veto flag
                candidate.metrics = Metrics(scores={
                    'fitness': float('-inf'), 
                    'protection_veto': 1.0,
                    'unused_dependencies_score': unused_methods_score,
                    'unused_methods_count': len(unused_methods_info['unused_methods'])
                })
                
                recommendations.append(
                    f"Rejected candidate {candidate.key()} for unused dependencies "
                    f"({len(unused_methods_info['unused_methods'])} methods)"
                )

        return {"recommendations": recommendations}

    def _detect_unused_methods(self, tree: ast.AST, candidate: Candidate) -> Dict[str, Any]:
        """Detect unused methods with comprehensive usage analysis including local function calls"""
        # Enhanced method detection with local function call tracking
        method_analyzer = MethodAnalyzer()
        method_analyzer.analyze(tree)
        
        unused_methods = []
        
        for method_key, method_info in method_analyzer.all_methods.items():
            class_name, method_name = method_key
            
            # Skip special methods and public methods (non-private)
            if (method_name.startswith('__') and method_name.endswith('__')) or not method_name.startswith('_'):
                continue
            
            # Enhanced usage check with multiple detection strategies
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
        
        return {
            'unused_methods': unused_methods,
            'all_methods': method_analyzer.all_methods,
            'all_calls': method_analyzer.get_all_calls(),
            'local_function_calls': method_analyzer.local_function_calls,
            'debug_info': method_analyzer.get_debug_info(),
            'candidate_key': candidate.key()
        }

    def _is_method_used_enhanced(self, class_name: str, method_name: str, 
                                analyzer: 'MethodAnalyzer') -> bool:
        """Enhanced method usage detection with local function call support"""
        
        # Strategy 1: Direct calls within the same class (self.method() or method())
        if (class_name, method_name) in analyzer.local_method_calls:
            return True
        
        # Strategy 2: Local function calls (method called as local function)
        if method_name in analyzer.local_function_calls.get(class_name, set()):
            return True
        
        # Strategy 3: Method calls on self
        if (class_name, method_name) in analyzer.self_method_calls:
            return True
        
        # Strategy 4: Method calls on class instances
        if (class_name, method_name) in analyzer.instance_method_calls:
            return True
        
        # Strategy 5: Static method calls (Class().method() pattern)
        if (class_name, method_name) in analyzer.static_style_calls:
            return True
        
        # Strategy 6: Method name appears in any call context
        if method_name in analyzer.method_names_called:
            return True
        
        # Strategy 7: Method referenced as attribute (not called)
        if method_name in analyzer.attribute_references:
            return True
        
        # Strategy 8: Method name referenced as string (getattr, etc.)
        if method_name in analyzer.string_method_references:
            return True
        
        # Strategy 9: Method called through dynamic invocation patterns
        if method_name in analyzer.dynamic_calls:
            return True
        
        return False

    def _log_detailed_unused_info(self, candidate: Candidate, methods_info: Dict):
        """Log detailed information about unused dependencies with enhanced debugging"""
        candidate_key = candidate.key()
        
        self.logger.warning(f"UNUSED DEPENDENCIES: {len(methods_info['unused_methods'])} methods in {candidate_key}")
        
        # Log unused methods
        if methods_info['unused_methods']:
            # Detailed list available at DEBUG level
            self.logger.debug(f"UNUSED METHODS ({len(methods_info['unused_methods'])} found):")
            for i, method_info in enumerate(methods_info['unused_methods'], 1):
                full_sig = method_info['full_signature']
                line_num = method_info['line_number']
                self.logger.debug(f"  {i}. Line {line_num}: {full_sig}")
        
        # Enhanced debug information
        if methods_info['unused_methods'] or self.logger.level <= logging.DEBUG:
            debug_info = methods_info.get('debug_info', {})
            self.logger.debug(f"ENHANCED DEBUG INFO:")
            self.logger.debug(f"  Total methods found: {len(methods_info['all_methods'])}")
            self.logger.debug(f"  Total calls found: {len(methods_info['all_calls'])}")
            self.logger.debug(f"  Local function calls: {len(methods_info.get('local_function_calls', {}))}")
            
            # Show local function calls per class for debugging
            local_calls = methods_info.get('local_function_calls', {})
            for class_name, calls in local_calls.items():
                if calls:
                    self.logger.debug(f"  Local calls in {class_name}: {list(calls)}")
            
            # Show some example calls for debugging
            example_calls = list(methods_info['all_calls'])[:8]
            if example_calls:
                self.logger.debug(f"  Example calls detected: {example_calls}")
        
        # Log summary
        total_issues = len(methods_info['unused_methods'])
        self.logger.warning(f"SUMMARY: {total_issues} unused method(s)")


class MethodAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.all_methods = {}  # {(class_name, method_name): method_info}
        self.current_class = None
        self.current_method = None
        
        # Call tracking with enhanced detection
        self.local_method_calls = set()  # (class_name, method_name) for calls within same class
        self.local_function_calls = {}  # {class_name: set(method_names)} for local function style calls
        self.self_method_calls = set()  # (class_name, method_name) for self.method()
        self.instance_method_calls = set()  # (class_name, method_name) for obj.method()
        self.static_style_calls = set()  # (class_name, method_name) for Class().method()
        self.method_names_called = set()  # All method names that appear in calls
        self.attribute_references = set()  # Method names accessed as attributes
        self.string_method_references = set()  # Method names referenced as strings
        self.dynamic_calls = set()  # Method names in dynamic call patterns
        
        # Context tracking
        self.class_stack = []
        self.method_stack = []

    def analyze(self, tree: ast.AST):
        """Main analysis entry point"""
        self.visit(tree)
        
    def get_all_calls(self) -> set:
        """Get all detected calls for debugging"""
        all_calls = set()
        all_calls.update(f"{cls}.{method}" for cls, method in self.local_method_calls)
        all_calls.update(f"self.{method}" for cls, method in self.self_method_calls)
        all_calls.update(f"{cls}().{method}" for cls, method in self.static_style_calls)
        all_calls.update(f"local_{method}" for method_set in self.local_function_calls.values() for method in method_set)
        all_calls.update(f"attr_{attr}" for attr in self.attribute_references)
        return all_calls
    
    def get_debug_info(self) -> Dict[str, Any]:
        """Get debug information"""
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
        """Track class context"""
        self.class_stack.append(node.name)
        self.current_class = node.name
        
        # Initialize local function calls tracking for this class
        if self.current_class not in self.local_function_calls:
            self.local_function_calls[self.current_class] = set()
        
        self.generic_visit(node)
        
        self.class_stack.pop()
        self.current_class = self.class_stack[-1] if self.class_stack else None

    def visit_FunctionDef(self, node):
        """Track method definitions and context"""
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
        """Enhanced call detection with local function call support"""
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr
            self.method_names_called.add(method_name)
            
            # Case 1: self.method()
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
                if self.current_class:
                    self.self_method_calls.add((self.current_class, method_name))
                    self.local_method_calls.add((self.current_class, method_name))
            
            # Case 2: obj.method() where obj is a variable
            elif isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                # Try to infer if this could be a same-class method call
                if self.current_class and obj_name.lower() == self.current_class.lower():
                    self.instance_method_calls.add((self.current_class, method_name))
            
            # Case 3: Class().method() - constructor call followed by method
            elif isinstance(node.func.value, ast.Call):
                if isinstance(node.func.value.func, ast.Name):
                    class_name = node.func.value.func.id
                    self.static_style_calls.add((class_name, method_name))
                    if class_name == self.current_class:
                        self.local_method_calls.add((class_name, method_name))

        elif isinstance(node.func, ast.Name):
            # Case 4: CRITICAL - Direct function calls that might be local methods
            function_name = node.func.id
            if self.current_class:
                # Check if this function name matches a method in the current class
                method_key = (self.current_class, function_name)
                if method_key in self.all_methods or function_name.startswith('_'):
                    # This is likely a local method call without self
                    self.local_function_calls[self.current_class].add(function_name)
                    self.local_method_calls.add((self.current_class, function_name))

        self.generic_visit(node)

    def visit_Attribute(self, node):
        """Track attribute access that might be method references"""
        if hasattr(node, 'attr'):
            self.attribute_references.add(node.attr)
            
            # Special case: accessing methods as attributes within the same class
            if isinstance(node.value, ast.Name) and node.value.id == 'self' and self.current_class:
                # This is self.attribute_name access
                if node.attr.startswith('_'):  # Likely a method
                    self.local_method_calls.add((self.current_class, node.attr))
                    
        self.generic_visit(node)

    def visit_Str(self, node):
        """Track string literals that might reference methods"""
        if hasattr(node, 's') and isinstance(node.s, str):
            # Check if string looks like a method name
            if node.s.startswith('_') and node.s.replace('_', '').isalnum():
                self.string_method_references.add(node.s)
                # Also track as potential dynamic call
                self.dynamic_calls.add(node.s)

    def visit_Constant(self, node):
        """Track constant string literals (Python 3.8+)"""
        if isinstance(node.value, str):
            # Check if string looks like a method name
            if node.value.startswith('_') and node.value.replace('_', '').isalnum():
                self.string_method_references.add(node.value)
                self.dynamic_calls.add(node.value)
        self.generic_visit(node)