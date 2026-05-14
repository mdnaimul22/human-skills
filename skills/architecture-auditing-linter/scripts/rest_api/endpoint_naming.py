import re
from typing import Any, List
from helpers.tool import Tool

VERB_LIST = {
    'get', 'fetch', 'list', 'create', 'add', 'post', 'update', 'put', 'delete', 
    'remove', 'patch', 'check', 'verify', 'send', 'generate', 'export', 'import',
    'submit', 'process', 'retrieve', 'find', 'search', 'query', 'sync', 'publish'
}

CRUD_NOUNS = {'creation', 'deletion', 'updation', 'removal', 'getter', 'fetcher'}
TECHNICAL_KEYWORDS = {
    'api', 'health', 'status', 'metrics', 'me', 'news', 'series', 'species', 'data', 
    'info', 'meta', 'config', 'metrics', 'search', 'filter', 'profile', 'avatar', 
    'settings', 'sync', 'people', 'index', 'login', 'auth', 'callback', 
    'webhook', 'ping', 'upload', 'download', 'token'
}
EXTENSIONS = {'.json', '.xml', '.csv', '.html', '.pdf', '.txt', '.yml', '.yaml'}
COMMON_ACTIONS = {
    'activate', 'deactivate', 'publish', 'approve', 'resend', 'sync', 
    'recalculate', 'verify', 'submit', 'process', 'export', 'import'
}
SPECIAL_CHARS = r'[!@#\$%\^&\*\(\)\+=\|\\\[\]\{\};:\'\",<>\?]'

ROUTE_DECORATORS = {
    'flask': re.compile(r'@(?:\w+\.)?route\(["\']([^"\']+)["\']'),
    'fastapi': re.compile(r'@(?:\w+\.)?(get|post|put|delete|patch)\(["\']([^"\']+)["\']'),
    'gin': re.compile(r'\.(?:GET|POST|PUT|DELETE|PATCH)\(\s*["\']([^"\']+)["\']'),
    'spring': re.compile(r'@(?:Get|Post|Put|Delete|Patch)Mapping\(\s*["\']([^"\']+)["\']'),
    'django': re.compile(r'path\(\s*["\']([^"\']+)["\']'),
    'express': re.compile(r'(?:app|router)\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'),
}

def _extract_endpoints(source_code: str) -> List[dict]:
    endpoints = []
    for fw, pattern in ROUTE_DECORATORS.items():
        for match in pattern.finditer(source_code):
            endpoints.append({'path': match.groups()[-1], 'fw': fw})
    return endpoints

def _score_endpoint(path: str, fw: str) -> float:
    score = 1.0
    deductions = []
    
    if '//' in path: deductions.append(0.20)
    if '?' in path: deductions.append(0.25)
    if path.endswith('/') and len(path) > 1:
        if fw != 'django': deductions.append(0.10)
    
    clean_path = path.split('?')[0].strip('/')
    raw_segments = [s for s in clean_path.split('/') if s]
    
    path_has_camel, path_has_snake, path_has_upper = False, False, False
    in_actions_namespace = False
    
    param_count = 0
    for i, seg in enumerate(raw_segments):
        seg_has_ext = False
        ext_found = next((e for e in EXTENSIONS if seg.lower().endswith(e)), None)
        
        name = seg
        if ext_found:
            deductions.append(0.20)
            name = name[:-len(ext_found)]
            seg_has_ext = True

        is_param = (name.startswith('{') and name.endswith('}')) or name.startswith(':') or (name.startswith('<') and name.endswith('>'))
        name_clean = name.strip('{}<>:').split(':')[-1]
        
        if is_param:
            param_count += 1
            if re.search(r'[a-z][A-Z]', name_clean) or any(c.isupper() for c in name_clean): deductions.append(0.10)
            if len(name_clean) <= 1 or (name_clean.lower().startswith('id') and len(name_clean) > 2 and re.search(r'\d$', name_clean)): deductions.append(0.10)
            if param_count == 1 and i > 0:
                prev = raw_segments[i-1].lower().strip('{}<>:').rstrip('s')
                if name_clean.lower() == f"{prev}_id" and name_clean.lower() != 'id': deductions.append(0.05)
            continue

        if re.match(r'^v(\d+)$', name.lower()):
            if i != 0: deductions.append(0.10)
            continue
        
        if re.match(r'^version\d+$', name.lower()):
            deductions.append(0.15)
            if i != 0: deductions.append(0.10)
            continue
        elif re.match(r'^v[\d\.]+$', name.lower()) or re.match(r'^v[a-zA-Z]+$', name.lower()):
            deductions.append(0.10)
            if i != 0: deductions.append(0.10)
            continue

        if name.lower() == 'actions':
            in_actions_namespace = True
            continue

        has_spec = False
        if not seg_has_ext:
            if bool(re.search(SPECIAL_CHARS + r'|\.', name)): has_spec = True
        else:
            if bool(re.search(SPECIAL_CHARS, name)): has_spec = True
        if has_spec: deductions.append(0.20)

        words = re.findall(r'[a-zA-Z0-9]+', re.sub(r'([a-z])([A-Z])', r'\1 \2', name.replace('-', ' ').replace('_', ' ').replace('.', ' ')))
        
        seg_has_verb = False
        if not has_spec:
            if name.lower() in COMMON_ACTIONS:
                if not in_actions_namespace: deductions.append(0.15)
            else:
                v_count = sum(1 for w in words if w.lower() in VERB_LIST and w.lower() not in TECHNICAL_KEYWORDS)
                if v_count > 0: 
                    deductions.append(0.25 * v_count)
                    seg_has_verb = True

        seg_has_crud = False
        if any(n in name.lower() for n in CRUD_NOUNS): 
            deductions.append(0.20)
            seg_has_crud = True

        if re.search(r'[a-z][A-Z]', name): path_has_camel = True
        if '_' in name: path_has_snake = True
        if any(c.isupper() for c in name) and not re.search(r'[a-z][A-Z]', name): path_has_upper = True

        if (name.lower() not in TECHNICAL_KEYWORDS and 
            not has_spec and
            not seg_has_ext and
            not in_actions_namespace):
            
            name_clean = name.lower().replace('-', '').replace('_', '')
            if not name_clean.endswith('s') and len(name_clean) > 2:
                is_last = (i == len(raw_segments) - 1)
                next_is_param = (i+1 < len(raw_segments) and (raw_segments[i+1].startswith('{') or raw_segments[i+1].startswith(':') or raw_segments[i+1].startswith('<')))
                if is_last or next_is_param:
                    non_action_words = [w for w in words if w.lower() not in VERB_LIST and w.lower() not in CRUD_NOUNS and w.lower() not in COMMON_ACTIONS]
                    if non_action_words:
                        if any(not w.lower().endswith('s') and len(w) > 2 for w in non_action_words):
                            if not (seg_has_verb or seg_has_crud) or path_has_snake:
                                deductions.append(0.15)

    if path_has_camel: deductions.append(0.20)
    elif path_has_upper: deductions.append(0.20)
    if path_has_snake and not path_has_camel: deductions.append(0.10)
    if len(raw_segments) > 6: deductions.append(0.10 * (len(raw_segments) - 6))
    
    if fw == 'spring' and path_has_camel: return 0.80
    total_deductions = sum(deductions)
    if total_deductions >= 0.95:
        return 0.0
    return round(max(0.0, score - total_deductions), 4)

class EndpointNamingConvention(Tool):
    def __init__(self):
        super().__init__(
            name="endpoint_naming_convention",
            description="Evaluates REST API endpoint naming conventions."
        )

    def evaluate(self, module: Any, source_code: str) -> float:
        meta = _extract_endpoints(source_code)
        if not meta:
            paths = re.findall(r'["\'](/[a-zA-Z0-9_\-\./{}/:]+)["\']', source_code)
            meta = [{'path': p, 'fw': 'generic'} for p in paths if len(p) > 1]
        if not meta: return 1.0
        scores = [_score_endpoint(m['path'], m['fw']) for m in meta]
        return round(sum(scores) / len(scores), 4)