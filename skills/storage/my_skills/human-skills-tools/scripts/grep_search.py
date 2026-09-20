import os
import re
import fnmatch
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass
from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error

@dataclass
class SearchResult:
    file_path: str
    line_number: Optional[int] = None
    line_content: Optional[str] = None
    node_path: Optional[str] = None
    context_type: Optional[str] = None
    snippet: Optional[str] = None

class GrepSearch(Tool):
    _cache = {}
    _exts = {"py", "js", "ts", "jsx", "tsx", "html", "css", "md", "java", "c", "cpp", "go", "rb", "php", "sh", "json", "xml", "yaml", "yml", "txt", "log", "sql", "r", "scala", "kt", "swift", "dart", "vue", "svelte"}
    _patterns = {
        "py": [
            (re.compile(r'^\s*class\s+([a-zA-Z0-9_]+)'), "class"),
            (re.compile(r'^\s*def\s+([a-zA-Z0-9_]+)'), "function"),
            (re.compile(r'^\s*async\s+def\s+([a-zA-Z0-9_]+)'), "async_function")
        ],
        "js": [
            (re.compile(r'^\s*class\s+([a-zA-Z0-9_$]+)'), "class"),
            (re.compile(r'^\s*function\s+([a-zA-Z0-9_$]+)'), "function"),
            (re.compile(r'^\s*const\s+([a-zA-Z0-9_$]+)\s*=\s*\([^)]*\)\s*=>'), "arrow_function"),
            (re.compile(r'^\s*([a-zA-Z0-9_$]+)\s*:\s*function'), "method")
        ]
    }
    
    async def execute(self, **kwargs) -> Response:
        path = kwargs.get("search_path", ".")
        query = kwargs.get("query")
        case_insensitive = kwargs.get("case_insensitive", False)
        match_per_line = kwargs.get("match_per_line", True)
        includes = kwargs.get("includes", [])
        
        if not query:
            return Response(message="Error: query parameter required", break_loop=False)
        
        if not os.path.exists(path):
            return Response(message=f"Error: Path '{path}' does not exist", break_loop=False)
        
        try:
            results = self._search(path, query, case_insensitive, match_per_line, includes)
            response = self._format(results, query, path, match_per_line)
            self.log.update(content=f"Searched '{query}' in {path} ({len(results)} matches)")
            return Response(message=response, break_loop=False)
        except Exception as e:
            handle_error(e)
            return Response(message=f"Error: {str(e)}", break_loop=False)
    
    def _search(self, path, query, case_insensitive, match_per_line, includes) -> List[SearchResult]:
        results = []
        files = self._get_files(path, includes)
        flags = re.IGNORECASE if case_insensitive else 0
        pattern = re.compile(re.escape(query), flags)
        
        for f in files:
            try:
                content = self._read_file(f)
                if not content:
                    continue
                    
                if match_per_line:
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            result = SearchResult(
                                file_path=f,
                                line_number=i + 1,
                                line_content=line.strip(),
                                snippet=self._get_snippet(lines, i)
                            )
                            self._context(result, lines)
                            results.append(result)
                else:
                    if pattern.search(content):
                        results.append(SearchResult(file_path=f))
            except Exception:
                continue
                
        return results[:100]
    
    def _get_files(self, path, includes) -> List[str]:
        files = []
        patterns = [f"*.{ext}" for ext in self._exts]
        if includes:
            patterns.extend(includes)
        
        if os.path.isfile(path):
            return [path] if self._match_patterns(path, patterns) else []
        
        for root, dirs, filenames in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in {'node_modules', '__pycache__', 'venv', 'env', '.git'}]
            for filename in filenames:
                if filename.startswith('.'):
                    continue
                filepath = os.path.join(root, filename)
                if self._match_patterns(filepath, patterns):
                    files.append(filepath)
                    
        return files
    
    def _match_patterns(self, filepath, patterns) -> bool:
        return any(fnmatch.fnmatch(filepath, p) for p in patterns)
    
    def _read_file(self, filepath) -> Optional[str]:
        if filepath in self._cache:
            return self._cache[filepath]
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    content = f.read()
                    if len(content) > 1000000:
                        continue
                    self._cache[filepath] = content
                    return content
            except:
                continue
        return None
    
    def _get_snippet(self, lines, line_idx, context=3) -> str:
        start = max(0, line_idx - context)
        end = min(len(lines), line_idx + context + 1)
        snippet_lines = []
        
        for i in range(start, end):
            prefix = ">>>" if i == line_idx else "   "
            snippet_lines.append(f"{prefix} {i+1:4d}: {lines[i]}")
            
        return "\n".join(snippet_lines)
    
    def _context(self, result, lines):
        if not result.line_number:
            return
            
        line_idx = result.line_number - 1
        ext = os.path.splitext(result.file_path)[1][1:].lower()
        
        if ext not in self._patterns:
            result.context_type = "file"
            result.node_path = os.path.basename(result.file_path)
            return
        
        context_stack = []
        current_indent = len(lines[line_idx]) - len(lines[line_idx].lstrip()) if line_idx < len(lines) else 0
        
        for i in range(line_idx - 1, -1, -1):
            if i >= len(lines):
                continue
            line = lines[i]
            if not line.strip():
                continue
                
            indent = len(line) - len(line.lstrip())
            
            for pattern, ctx_type in self._patterns[ext]:
                match = pattern.search(line)
                if match:
                    name = match.group(1)
                    if indent <= current_indent:
                        context_stack = [(name, ctx_type, indent)] + [c for c in context_stack if c[2] < indent]
                        current_indent = indent
                        break
            
            if indent == 0 and context_stack:
                break
        
        if context_stack:
            if len(context_stack) > 1:
                class_ctx = next((c for c in context_stack if c[1] == "class"), None)
                func_ctx = next((c for c in context_stack if c[1] in ["function", "method", "async_function"]), None)
                
                if class_ctx and func_ctx:
                    result.node_path = f"{class_ctx[0]}.{func_ctx[0]}"
                    result.context_type = "method"
                else:
                    result.node_path = context_stack[0][0]
                    result.context_type = context_stack[0][1]
            else:
                result.node_path = context_stack[0][0]
                result.context_type = context_stack[0][1]
        else:
            result.node_path = os.path.basename(result.file_path)
            result.context_type = "module"
    
    def _format(self, results, query, path, match_per_line) -> str:
        if not results:
            return f"No matches for '{query}' in {path}"
        
        parts = [f"Found {len(results)} matches for '{query}' in {path}\n"]
        
        if match_per_line:
            files = {}
            for r in results:
                files.setdefault(r.file_path, []).append(r)
            
            for filepath, file_results in list(files.items())[:10]:
                rel_path = os.path.relpath(filepath, path) if path != "." else filepath
                parts.append(f"\n**{rel_path}**")
                
                for r in file_results[:5]:
                    ctx = f" ({r.context_type} `{r.node_path}`)" if r.node_path and r.context_type != "module" else ""
                    parts.append(f"\nLine {r.line_number}{ctx}:")
                    parts.append(f"`{r.line_content}`")
                    
                    if r.snippet:
                        parts.append(f"```\n{r.snippet}\n```")
                
                if len(file_results) > 5:
                    parts.append(f"\n[{len(file_results) - 5} more matches in this file]")
        else:
            for r in results[:20]:
                rel_path = os.path.relpath(r.file_path, path) if path != "." else r.file_path
                parts.append(f"- {rel_path}")
        
        if len(results) > (200 if match_per_line else 20):
            parts.append(f"\n[{len(results) - (200 if match_per_line else 20)} more matches not shown]")
        
        return "\n".join(parts)