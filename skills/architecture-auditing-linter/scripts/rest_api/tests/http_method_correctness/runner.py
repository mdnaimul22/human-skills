import sys
import os
from pathlib import Path

# Add necessary directories to sys.path
current_dir = Path(__file__).resolve().parent
# Path to the tools (scripts/rest_api/)
sys.path.append(str(current_dir.parent.parent))
# Path to helpers (inside skills/ directory)
# Root is 5 levels up: http_method_correctness(0), tests(1), rest_api(2), scripts(3), architecture-auditing-linter(4), skills(5)
skills_dir = current_dir.parents[4]
sys.path.append(str(skills_dir))

try:
    from http_method import HttpMethodCorrectness
    from cases import EXTENDED_TEST_CASES as TEST_CASES
except ImportError as e:
    print(f"Error: {e}")
    print(f"Python Path: {sys.path}")
    sys.exit(1)

def run_benchmarks():
    tool = HttpMethodCorrectness()
    print(f"{'ID':<20} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 65)
    
    passed = 0
    for case in TEST_CASES:
        actual_score = tool.evaluate(None, case["code"])
        
        # Tolerance check (since scoring can be floating point)
        diff = abs(actual_score - case["expected_score"])
        status = "✅ PASS" if diff < 0.1 else "❌ FAIL"
        
        if status == "✅ PASS":
            passed += 1
            
        print(f"{case['id']:<20} | {case['expected_score']:<10} | {actual_score:<10} | {status}")
        if status == "❌ FAIL":
            print(f"   Reason: {case['description']}")

    print("-" * 65)
    print(f"Result: {passed}/{len(TEST_CASES)} passed.")

if __name__ == "__main__":
    run_benchmarks()
