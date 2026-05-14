import re

JSON_ERROR_RESPONSE = re.compile(
    r'\b(jsonify\s*\(\s*\{|JSONResponse\s*\(\s*\{|'
    r'{"error"|{"message"|{"detail"|"status_code")\b',
    re.IGNORECASE,
)

TRACEBACK_LEAK = re.compile(
    r'\b(traceback\.print_exc|traceback\.format_exc.*return|'
    r'str\(e\).*return|repr\(e\).*return)\b',
    re.IGNORECASE,
)

code_leak = 'return {"error": traceback.format_exc()}'
code_json = 'return jsonify({"error": "msg"})'

print(f"Leak Match: {bool(TRACEBACK_LEAK.search(code_leak))}")
print(f"JSON Match: {bool(JSON_ERROR_RESPONSE.search(code_json))}")

# Check specificity for perfect_handling
# IntegrityError matches SPECIFIC_EXCEPTIONS?
SPECIFIC_EXCEPTIONS = re.compile(
    r'except\s+(ValueError|TypeError|KeyError|IndexError|AttributeError|'
    r'RuntimeError|OSError|IOError|FileNotFoundError|PermissionError|'
    r'NotFoundError|ValidationError|IntegrityError|OperationalError|'
    r'ConnectionError|TimeoutError|HTTPException|RequestException)\s*',
    re.IGNORECASE,
)
code_spec = 'except IntegrityError as e:'
print(f"Spec Match: {bool(SPECIFIC_EXCEPTIONS.search(code_spec))}")
