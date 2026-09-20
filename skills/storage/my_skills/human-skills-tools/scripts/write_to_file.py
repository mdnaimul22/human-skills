import os
import ast
import json
import tempfile
import subprocess
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from python.helpers.tool import Tool, Response
from python.helpers.print_style import PrintStyle
from python.helpers.errors import handle_error

@dataclass
class ErrorCheckResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class WriteToFile(Tool):
    """Tool for creating new files with content and automatic syntax validation."""
    
    def __init__(self, agent=None, name="write_to_file", method="execute", args=None, message="Create new files with content", **kwargs):
        super().__init__(agent=agent, name=name, method=method, args=args or {}, message=message, **kwargs)
        self.error_checkers = {
            '.py': self._check_python_syntax,
            '.js': self._check_javascript_syntax,
            '.json': self._check_json_syntax,
            '.yaml': self._check_yaml_syntax,
            '.yml': self._check_yaml_syntax,
            '.xml': self._check_xml_syntax,
            '.html': self._check_html_syntax,
        }
    
    def _check_python_syntax(self, content: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        if not content.strip():
            return ErrorCheckResult(True, [], [], [])
        
        try:
            ast.parse(content)
        except SyntaxError as e:
            errors.append(f"Python syntax error: {e.msg} at line {e.lineno}")
        except Exception as e:
            errors.append(f"Python parsing error: {str(e)}")
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            if line_stripped.endswith(':') and not line_stripped.startswith(('#', '"', "'")):
                if i < len(lines) and lines[i].strip() and not lines[i].startswith((' ', '\t')):
                    # Skip warning if next line is a docstring (triple quotes)
                    next_line_stripped = lines[i].strip() if i < len(lines) else ''
                    if not (next_line_stripped.startswith('"""') or next_line_stripped.startswith("'''")):
                        warnings.append(f"Line {i}: Missing indentation after colon")
            
            if line_stripped.startswith('def ') and not line_stripped.endswith(':'):
                # Check if this is a multi-line function definition (has opening parenthesis)
                def_pos = line_stripped.find('def ')
                if def_pos != -1:
                    after_def = line_stripped[def_pos + 4:].strip()
                    # If there's no opening parenthesis, it's likely missing colon
                    # If there is an opening parenthesis, it's a multi-line definition (valid)
                    if '(' not in after_def:
                        errors.append(f"Line {i}: Function definition missing colon")
            
            if line_stripped.startswith('class ') and not line_stripped.endswith(':'):
                errors.append(f"Line {i}: Class definition missing colon")
            
            # Multi-line imports with unbalanced parentheses are valid Python syntax
            # Skip this check as it produces false positives for valid code
            # The AST parser will catch actual syntax errors
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _check_javascript_syntax(self, content: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        if not content.strip():
            return ErrorCheckResult(True, [], [], [])
        
        brackets = {'(': ')', '[': ']', '{': '}'}
        stack = []
        
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            for char in line:
                if char in brackets:
                    stack.append((char, i))
                elif char in brackets.values():
                    if not stack:
                        errors.append(f"Line {i}: Unmatched closing bracket '{char}'")
                    else:
                        open_char, open_line = stack.pop()
                        if brackets[open_char] != char:
                            errors.append(f"Line {i}: Mismatched bracket. Expected '{brackets[open_char]}', got '{char}'")
        
        if stack:
            for char, line_num in stack:
                errors.append(f"Line {line_num}: Unclosed bracket '{char}'")
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if line_stripped.startswith('function ') and not line_stripped.endswith('{'):
                if '{' not in line_stripped:
                    warnings.append(f"Line {i}: Function declaration might be missing opening brace")
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _check_json_syntax(self, content: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        if not content.strip():
            return ErrorCheckResult(True, [], [], [])
        
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            errors.append(f"JSON syntax error: {e.msg} at line {e.lineno}, column {e.colno}")
        except Exception as e:
            errors.append(f"JSON parsing error: {str(e)}")
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _check_yaml_syntax(self, content: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        if not content.strip():
            return ErrorCheckResult(True, [], [], [])
        
        try:
            import yaml
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            errors.append(f"YAML syntax error: {str(e)}")
        except ImportError:
            warnings.append("PyYAML not available for YAML syntax checking")
        except Exception as e:
            errors.append(f"YAML parsing error: {str(e)}")
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _check_xml_syntax(self, content: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        if not content.strip():
            return ErrorCheckResult(True, [], [], [])
        
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(content)
        except ET.ParseError as e:
            errors.append(f"XML syntax error: {str(e)}")
        except Exception as e:
            errors.append(f"XML parsing error: {str(e)}")
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _check_html_syntax(self, content: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        if not content.strip():
            return ErrorCheckResult(True, [], [], [])
        
        try:
            from html.parser import HTMLParser
            
            class HTMLValidator(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.errors = []
                    self.tag_stack = []
                
                def handle_starttag(self, tag, attrs):
                    if tag not in ['br', 'hr', 'img', 'input', 'meta', 'link']:
                        self.tag_stack.append(tag)
                
                def handle_endtag(self, tag):
                    if self.tag_stack and self.tag_stack[-1] == tag:
                        self.tag_stack.pop()
                    elif tag in self.tag_stack:
                        self.errors.append(f"Mismatched closing tag: {tag}")
                
                def error(self, message):
                    self.errors.append(f"HTML parsing error: {message}")
            
            validator = HTMLValidator()
            validator.feed(content)
            
            if validator.tag_stack:
                for tag in validator.tag_stack:
                    warnings.append(f"Unclosed HTML tag: {tag}")
            
            errors.extend(validator.errors)
            
        except ImportError:
            warnings.append("HTML parser not available for syntax checking")
        except Exception as e:
            warnings.append(f"HTML validation error: {str(e)}")
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _run_external_linter(self, file_path: str, temp_file_path: str) -> ErrorCheckResult:
        errors = []
        warnings = []
        suggestions = []
        
        file_ext = Path(file_path).suffix.lower()
        
        try:
            if file_ext == '.py':
                result = subprocess.run(['python', '-m', 'py_compile', temp_file_path], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode != 0:
                    errors.append(f"Python compilation error: {result.stderr.strip()}")
                
                try:
                    result = subprocess.run(['flake8', '--select=E9,F63,F7,F82', temp_file_path], 
                                          capture_output=True, text=True, timeout=10)
                    if result.stdout:
                        for line in result.stdout.strip().split('\n'):
                            if line:
                                warnings.append(f"Linter warning: {line}")
                except FileNotFoundError:
                    pass
                    
            elif file_ext == '.js':
                try:
                    result = subprocess.run(['node', '--check', temp_file_path], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        errors.append(f"JavaScript syntax error: {result.stderr.strip()}")
                except FileNotFoundError:
                    pass
                    
        except subprocess.TimeoutExpired:
            warnings.append("External linter timeout")
        except Exception as e:
            warnings.append(f"External linter error: {str(e)}")
        
        return ErrorCheckResult(len(errors) == 0, errors, warnings, suggestions)
    
    def _validate_syntax(self, content: str, file_path: str) -> ErrorCheckResult:
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in self.error_checkers:
            result = self.error_checkers[file_ext](content)
            
            if result.errors or result.warnings:
                with tempfile.NamedTemporaryFile(mode='w', suffix=file_ext, delete=False) as temp_file:
                    temp_file.write(content)
                    temp_file_path = temp_file.name
                
                try:
                    external_check = self._run_external_linter(file_path, temp_file_path)
                    result.errors.extend(external_check.errors)
                    result.warnings.extend(external_check.warnings)
                    result.suggestions.extend(external_check.suggestions)
                finally:
                    os.unlink(temp_file_path)
            
            return result
        else:
            return ErrorCheckResult(True, [], [f"No syntax checker available for {file_ext} files"], [])
    
    def _format_error_report(self, error_check: ErrorCheckResult, target_file: str) -> str:
        report_parts = [f"❌ BLOCKED: File creation failed for '{target_file}'"]
        
        if error_check.errors:
            report_parts.append(f"\n🚫 CRITICAL ERRORS (must fix):")
            for error in error_check.errors:
                report_parts.append(f"  × {error}")
        
        if error_check.warnings:
            report_parts.append(f"\n⚠️  Warnings:")
            for warning in error_check.warnings:
                report_parts.append(f"  ! {warning}")
        
        if error_check.suggestions:
            report_parts.append(f"\n💡 Suggestions:")
            for suggestion in error_check.suggestions:
                report_parts.append(f"  → {suggestion}")
        
        report_parts.append(f"\n🔧 Fix the syntax errors above and try again.")
        
        return '\n'.join(report_parts)
    
    def _format_success_report(self, target_file: str, content_length: int, error_check: Optional[ErrorCheckResult] = None) -> str:
        report_parts = [f"✅ Successfully created file: '{target_file}' ({content_length} bytes)"]
        
        if error_check:
            if not error_check.errors and not error_check.warnings:
                report_parts.append("✓ Syntax validation passed")
            elif error_check.warnings:
                report_parts.append(f"\n⚠️  Warnings detected (file created anyway):")
                for warning in error_check.warnings:
                    report_parts.append(f"  ! {warning}")
            
            if error_check.suggestions:
                report_parts.append(f"\n💡 Suggestions for improvement:")
                for suggestion in error_check.suggestions:
                    report_parts.append(f"  → {suggestion}")
        
        return '\n'.join(report_parts)

    async def execute(self, **kwargs) -> Response:
        target_file = kwargs.get("target_file")
        code_content = kwargs.get("code_content", "")
        empty_file = kwargs.get("empty_file", False)
        auto_check = kwargs.get("auto_check", True)
        strict_mode = kwargs.get("strict_mode", True)
        
        if not target_file:
            return Response(message="Error: target_file parameter is required", break_loop=False)
        
        if os.path.exists(target_file):
            return Response(
                message=f"Error: File '{target_file}' already exists. Use line_replace tool to modify existing files.", 
                break_loop=False
            )
        
        parent_dir = os.path.dirname(target_file)
        if parent_dir and not os.path.exists(parent_dir):
            try:
                os.makedirs(parent_dir, exist_ok=True)
                self.log.update(content=f"Created directory: {parent_dir}")
            except Exception as e:
                handle_error(e)
                return Response(message=f"Error creating directory: {str(e)}", break_loop=False)
        
        if empty_file:
            try:
                with open(target_file, 'w', encoding='utf-8') as f:
                    pass
                self.log.update(content=f"Created empty file: {target_file}")
                return Response(message=f"✅ Successfully created empty file: {target_file}", break_loop=False)
            except Exception as e:
                handle_error(e)
                return Response(message=f"Error creating file: {str(e)}", break_loop=False)
        
        error_check_result = None
        if auto_check and code_content.strip():
            error_check_result = self._validate_syntax(code_content, target_file)
            
            if strict_mode and error_check_result.errors:
                error_report = self._format_error_report(error_check_result, target_file)
                return Response(message=error_report, break_loop=False)
        
        try:
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            content_length = len(code_content)
            self.log.update(content=f"Created file: {target_file} ({content_length} bytes)")
            
            success_message = self._format_success_report(target_file, content_length, error_check_result)
            return Response(message=success_message, break_loop=False)
                
        except Exception as e:
            handle_error(e)
            return Response(message=f"Error creating file: {str(e)}", break_loop=False)