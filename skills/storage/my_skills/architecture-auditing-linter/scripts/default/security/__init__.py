"""
OpenScore Security Detector Framework.

All security detectors in this package must inherit from `SecurityDetector` 
and implement the `detect()` method. The `security_ssrc.py` tool will 
dynamically discover and load all detectors from this directory.

Adding a new detector:
    1. Create a new file: security/<name>_risk.py
    2. Define a class inheriting from SecurityDetector
    3. Implement detect(tree, source_code) → List[SecurityIssue]
    4. Run `python main.py sync`
"""

import ast
from typing import List


# ──────────────────────────────────────────────
# Severity Constants
# ──────────────────────────────────────────────
CRITICAL = "CRITICAL"
HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"

SEVERITY_PENALTY = {
    CRITICAL: 0.40,
    HIGH: 0.25,
    MEDIUM: 0.08,
    LOW: 0.02,
}


class SecurityIssue:
    """A single security finding with severity, location, category, and message."""
    __slots__ = ('severity', 'line', 'category', 'message')

    def __init__(self, severity: str, line: int, category: str, message: str):
        self.severity = severity
        self.line = line
        self.category = category
        self.message = message

    def to_suggestion(self) -> str:
        return f"Line {self.line}: [{self.severity}] [{self.category}] {self.message}"

    def __repr__(self) -> str:
        return f"SecurityIssue({self.severity}, L{self.line}, {self.category})"


class SecurityDetector:
    """
    Base class for all security detectors.
    
    Subclasses MUST:
        - Set `name` and `description` class attributes
        - Implement `detect(tree: ast.AST, source_code: str) -> List[SecurityIssue]`
    
    The `detect` method receives both the parsed AST tree and raw source code,
    allowing detectors to use AST analysis, regex, or both.
    """
    
    name: str = "base"
    description: str = "Base security detector"

    def detect(self, tree: ast.AST, source_code: str) -> List[SecurityIssue]:
        """
        Analyze code and return a list of SecurityIssues found.
        
        Args:
            tree: Parsed AST tree of the source code.
            source_code: Raw source code string.
            
        Returns:
            List of SecurityIssue objects.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement detect()")
