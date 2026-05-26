import re
import ast
from typing import Any, List, Tuple
from helpers.tool import Tool

COMBINED_ROUTE_PATTERN = re.compile(
    r'(?:@(?P<fw_decorator>(?:app|router|api|blueprint|app\.route))\.(?P<fw_method>get|post|put|patch|delete|route)\s*\(\s*["\'](?P<fw_path>[^"\']+)["\'](?:.*methods\s*=\s*\[(?P<fw_methods_list>.*?)\])?)|'
    r'(?:@(?P<spring_decorator>GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping)\s*\(\s*["\'](?P<spring_path>[^"\']+)["\'])|'
    r'(?:(?P<js_obj>router|app|api|r)\.(?P<js_method>GET|POST|PUT|PATCH|DELETE|get|post|put|patch|delete)\s*\(\s*["\'](?P<js_path>[^"\']+)["\'])|'
    r'(?:class\s+\w+(?:View|Controller|Handler).*?def\s+(?P<class_method>get|post|put|patch|delete)\b)',
    re.IGNORECASE | re.DOTALL
)

MUTATION_METHODS = {
    'insert', 'insert_one', 'insert_many', 'update', 'update_one', 'update_many',
    'delete', 'delete_one', 'delete_many', 'replace_one', 'upsert', 'save', 'create',
    'remove', 'modify', 'patch', 'push', 'pull', 'inc', 'set', 'unset', 'replace',
    'save_all', 'delete_all', 'update_all', 'save_and_flush', 'delete_in_batch',
    'deletebyid', 'saveandflush', 'persist', 'merge', 'send', 'publish', 'trigger',
    'charge', 'process', 'execute', 'run', 'commit', 'rollback', 'flush', 'sync',
    'clear', 'purge', 'revoke', 'atomic', 'begin', 'with_for_update', 'lock'
}

WEAK_MUTATION_KEYWORDS = {
    'views', 'counter', 'last_login', 'last_update', 'generated_at', 'inc', 'if', 'not', 'cache', 'commit', 'lock', 'transaction'
}

class _MutationVisitor(ast.NodeVisitor):
    def __init__(self):
        self.has_strong = False
        self.has_weak = False
        self.has_read = False
        self.in_if = False

    def visit_If(self, node: ast.If):
        old_in_if = self.in_if
        self.in_if = True
        self.generic_visit(node)
        self.in_if = old_in_if

    def visit_Call(self, node: ast.Call):
        func_name = ''
        if isinstance(node.func, ast.Attribute):
            func_name = node.func.attr
        elif isinstance(node.func, ast.Name):
            func_name = node.func.id
        
        lower_name = func_name.lower()
        if lower_name in MUTATION_METHODS:
            node_dump = ast.dump(node).lower()
            if self.in_if or any(kw in node_dump for kw in WEAK_MUTATION_KEYWORDS) or lower_name in ('commit', 'lock', 'with_for_update', 'flush'):
                self.has_weak = True
            else:
                self.has_strong = True
        
        if lower_name in ('find', 'find_one', 'find_many', 'get', 'filter', 'all', 'first', 'last', 'count', 'exists', 'aggregate', 'retrieve', 'map', 'query'):
            self.has_read = True
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        attr_name = node.attr.lower()
        if attr_name in ('save', 'delete', 'update', 'create'):
            if self.in_if: self.has_weak = True
            else: self.has_strong = True
        elif attr_name in ('commit', 'flush', 'lock'):
            self.has_weak = True
        self.generic_visit(node)

def _extract_method_handler_pairs(source_code: str) -> List[Tuple[str, str]]:
    matches = []
    for match in COMBINED_ROUTE_PATTERN.finditer(source_code):
        start = match.start()
        gd = match.groupdict()
        methods = []
        if gd.get('fw_method'):
            m = gd['fw_method'].upper()
            if m == 'ROUTE' and gd.get('fw_methods_list'):
                m_list = [x.strip().strip('"\u0027').upper() for x in gd['fw_methods_list'].split(',')]
                methods.extend(m_list)
            else: methods.append(m)
        elif gd.get('spring_decorator'):
            methods.append(gd['spring_decorator'].replace('Mapping', '').upper())
        elif gd.get('js_method'):
            methods.append(gd['js_method'].upper())
        elif gd.get('class_method'):
            methods.append(gd['class_method'].upper())
        for m in methods:
            matches.append({'method': m, 'start': start})

    if not matches: return []
    matches.sort(key=lambda x: x['start'])
    unique = []
    if matches:
        unique.append(matches[0])
        for i in range(1, len(matches)):
            if matches[i]['start'] - unique[-1]['start'] < 5: continue
            unique.append(matches[i])

    pairs = []
    for i in range(len(unique)):
        start = unique[i]['start']
        end = unique[i+1]['start'] if i + 1 < len(unique) else len(source_code)
        pairs.append((unique[i]['method'], source_code[start:end]))
    return pairs

class HttpMethodCorrectness(Tool):
    def __init__(self):
        super().__init__(
            name="http_method_correctness",
            description="Scores whether HTTP methods are used semantically correctly."
        )

    def evaluate(self, module: Any, source_code: str) -> tuple[float, list[str]]:
        pairs = _extract_method_handler_pairs(source_code)
        if not pairs: return 1.0, []

        scores = []
        all_suggestions = []
        for method, body in pairs:
            clean_body = re.sub(r'#.*', '', body)
            clean_body = re.sub(r'^\s*@.*\n', '', clean_body, flags=re.MULTILINE)
            
            try:
                tree = ast.parse(clean_body)
                visitor = _MutationVisitor()
                visitor.visit(tree)
                has_strong, has_weak, has_read = visitor.has_strong, visitor.has_weak, visitor.has_read
            except:
                has_strong = bool(re.search(r'(insert|delete|create|save|replace|update|commit|rollback|send|publish|charge|revoke)', clean_body, re.I))
                has_weak = bool(re.search(r'(views|counter|inc|last_login|not\s+found|if|cache|commit|lock|transaction)', clean_body, re.I))
                has_read = bool(re.search(r'(find|get|list|fetch|retrieve|all|select|exists|findById|map|query)', clean_body, re.I))

            if method == 'GET':
                if has_strong: 
                    scores.append(0.0)
                    all_suggestions.append(f"CRITICAL: Found strong database mutations in GET endpoint. GET must be strictly read-only.")
                elif has_weak: 
                    scores.append(0.5)
                    all_suggestions.append(f"Found weak mutations (like logging or cache updates) in GET endpoint. Ensure it remains safe/idempotent.")
                else: 
                    scores.append(1.0)
            elif method in ('POST', 'PUT', 'PATCH', 'DELETE'):
                if has_strong or has_weak: 
                    scores.append(1.0)
                elif has_read: 
                    scores.append(0.6)
                    all_suggestions.append(f"Found read-only logic in {method} endpoint. Use GET for fetching data.")
                else: 
                    scores.append(0.5)
            else: 
                scores.append(1.0)

        return (round(sum(scores) / len(scores), 4) if scores else 1.0), list(set(all_suggestions))