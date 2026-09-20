import os
import io
import mmap
import hashlib
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error
from python.helpers.messages import truncate_text

FILE_CACHE = {}
META_CACHE = {}
MAX_SIZE = 50 * 1024 * 1024
MAX_ENTRIES = 50
CHUNK_SIZE = 8192

def get_file_hash(path: str, size: int) -> str:
    if size < 1024:
        with open(path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    h = hashlib.md5()
    with open(path, 'rb') as f:
        h.update(f.read(512))
        f.seek(size // 2)
        h.update(f.read(512))
        f.seek(-min(512, size))
        h.update(f.read())
    return h.hexdigest()

def cleanup_cache():
    if len(FILE_CACHE) > MAX_ENTRIES:
        items = sorted(FILE_CACHE.items(), key=lambda x: x[1].get('last_access', 0))
        for k, v in items[:len(FILE_CACHE) - MAX_ENTRIES + 10]:
            del FILE_CACHE[k]

def detect_encoding(path: str) -> str:
    try:
        import chardet
        with open(path, 'rb') as f:
            raw = f.read(min(10000, os.path.getsize(path)))
        result = chardet.detect(raw)
        return result.get('encoding', 'utf-8') or 'utf-8'
    except:
        return 'utf-8'

def smart_read_lines(path: str, start: int = 1, count: Optional[int] = None) -> Tuple[List[str], int]:
    try:
        stat = os.stat(path)
        size = stat.st_size
        mtime = stat.st_mtime
        
        cache_key = f"{path}:{size}:{mtime}"
        
        if cache_key in FILE_CACHE:
            cache_entry = FILE_CACHE[cache_key]
            cache_entry['last_access'] = time.time()
            lines = cache_entry['lines']
            total = len(lines)
            
            zero_based_start = max(0, start - 1)
            if count is None:
                return lines[zero_based_start:], total
            return lines[zero_based_start:zero_based_start + count], total
        
        if size > MAX_SIZE:
            return read_large_file_lines(path, start, count)
        
        encoding = detect_encoding(path)
        
        try:
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            with open(path, 'r', encoding='latin1', errors='replace') as f:
                lines = f.readlines()
        
        FILE_CACHE[cache_key] = {
            'lines': lines,
            'last_access': time.time(),
            'size': size
        }
        
        cleanup_cache()
        
        total = len(lines)
        zero_based_start = max(0, start - 1)
        if count is None:
            return lines[zero_based_start:], total
        return lines[zero_based_start:zero_based_start + count], total
        
    except Exception as e:
        return [f"Error reading file: {str(e)}"], 0

def read_large_file_lines(path: str, start: int = 1, count: Optional[int] = None) -> Tuple[List[str], int]:
    encoding = detect_encoding(path)
    lines = []
    line_count = 0
    current_line = 1
    zero_based_start = max(0, start - 1)
    
    try:
        with open(path, 'r', encoding=encoding, errors='replace') as f:
            for line in f:
                if current_line > zero_based_start:
                    if count is None or len(lines) < count:
                        lines.append(line)
                    elif count is not None and len(lines) >= count:
                        break
                current_line += 1
            
            if count is None:
                for _ in f:
                    current_line += 1
                    
        return lines, current_line - 1
        
    except Exception as e:
        return [f"Error reading large file: {str(e)}"], 0

def analyze_file_structure(lines: List[str]) -> Dict[str, Any]:
    total = len(lines)
    if total == 0:
        return {}
    
    analysis = {
        'total_lines': total,
        'empty_lines': 0,
        'code_lines': 0,
        'comment_lines': 0,
        'functions': [],
        'classes': [],
        'imports': [],
        'language': 'unknown'
    }
    
    func_pattern = re.compile(r'^\s*(def|function|fun)\s+(\w+)', re.IGNORECASE)
    class_pattern = re.compile(r'^\s*(class|struct|interface)\s+(\w+)', re.IGNORECASE)
    import_pattern = re.compile(r'^\s*(import|from|#include|require)', re.IGNORECASE)
    comment_patterns = [
        re.compile(r'^\s*#'),
        re.compile(r'^\s*//'),
        re.compile(r'^\s*/\*'),
        re.compile(r'^\s*\*'),
        re.compile(r'^\s*--'),
        re.compile(r'^\s*;')
    ]
    
    for i, line in enumerate(lines[:min(1000, total)]):
        stripped = line.strip()
        
        if not stripped:
            analysis['empty_lines'] += 1
            continue
            
        is_comment = any(pattern.match(line) for pattern in comment_patterns)
        if is_comment:
            analysis['comment_lines'] += 1
        else:
            analysis['code_lines'] += 1
            
        func_match = func_pattern.match(line)
        if func_match:
            analysis['functions'].append({
                'name': func_match.group(2),
                'line': i + 1
            })
            
        class_match = class_pattern.match(line)
        if class_match:
            analysis['classes'].append({
                'name': class_match.group(2),
                'line': i + 1
            })
            
        if import_pattern.match(line):
            analysis['imports'].append({
                'line': i + 1,
                'content': stripped[:100]
            })
    
    if any(line.strip().startswith(('def ', 'import ', 'class ')) for line in lines[:50]):
        analysis['language'] = 'python'
    elif any(re.search(r'\b(function|var|let|const)\b', line) for line in lines[:50]):
        analysis['language'] = 'javascript'
    elif any(re.search(r'\b(public|private|class)\b.*\{', line) for line in lines[:50]):
        analysis['language'] = 'java'
    
    return analysis

class ViewFile(Tool):
    async def execute(self, **kwargs) -> Response:
        path = kwargs.get("absolute_path")
        
        if not path:
            return Response(message="Error: absolute_path is a required argument.", break_loop=False)
        
        if not os.path.isfile(path):
            return Response(message=f"Error: File '{path}' not found.", break_loop=False)
        
        try:
            lines, total_lines = smart_read_lines(path, start=1, count=None)
            
            # Handle empty file case
            if not lines and total_lines == 0:
                if os.path.getsize(path) == 0:
                     self.log.update(content=f"Viewed empty file: {path}")
                     return Response(message="", break_loop=False)
                else:
                     return Response(message=f"Error: Could not read any lines from '{path}', but file is not empty.", break_loop=False)

            # Handle error message returned from smart_read_lines
            if total_lines == 0 and lines and "Error reading file:" in lines[0]:
                return Response(message=lines[0], break_loop=False)

            numbered_lines = [f"{i + 1}: {line.rstrip('\n')}\n" for i, line in enumerate(lines)]
            response = "".join(numbered_lines)
            
            self.log.update(content=f"Viewed {total_lines} lines from {path}")
            
            # Keep truncation for very large files
            if len(response) > 100000:
                response = truncate_text(self.agent, response, 100000)
                response += "\n[Truncated due to size]"
                
            return Response(message=response, break_loop=False)
            
        except Exception as e:
            handle_error(e)
            return Response(message=f"An unexpected error occurred: {str(e)}", break_loop=False)

class FileStats(Tool):
    async def execute(self, **kwargs) -> Response:
        path = kwargs.get("absolute_path")
        
        if not path:
            return Response(message="Error: absolute_path required", break_loop=False)
        
        if not os.path.exists(path):
            return Response(message=f"Error: Path '{path}' not found", break_loop=False)
        
        try:
            stat = os.stat(path)
            
            parts = []
            parts.append(f"Path: {path}\n")
            parts.append(f"Type: {'File' if os.path.isfile(path) else 'Directory'}\n")
            parts.append(f"Size: {stat.st_size:,} bytes\n")
            parts.append(f"Modified: {time.ctime(stat.st_mtime)}\n")
            parts.append(f"Created: {time.ctime(stat.st_ctime)}\n")
            
            if os.path.isfile(path):
                try:
                    lines, total = smart_read_lines(path, 1, None)
                    analysis = analyze_file_structure(lines)
                    
                    parts.append(f"Lines: {total:,}\n")
                    parts.append(f"Language: {analysis.get('language', 'unknown')}\n")
                    parts.append(f"Functions: {len(analysis.get('functions', []))}\n")
                    parts.append(f"Classes: {len(analysis.get('classes', []))}\n")
                    parts.append(f"Imports: {len(analysis.get('imports', []))}\n")
                    
                    if analysis.get('functions'):
                        parts.append("\nFunctions:\n")
                        for func in analysis['functions'][:10]:
                            parts.append(f"  {func['name']} (line {func['line']})\n")
                    
                    if analysis.get('classes'):
                        parts.append("\nClasses:\n")
                        for cls in analysis['classes'][:10]:
                            parts.append(f"  {cls['name']} (line {cls['line']})\n")
                            
                except Exception as e:
                    parts.append(f"Analysis error: {str(e)}\n")
            
            response = "".join(parts)
            self.log.update(content=f"Stats for {path}")
            
            return Response(message=response, break_loop=False)
            
        except Exception as e:
            handle_error(e)
            return Response(message=f"Error: {str(e)}", break_loop=False)