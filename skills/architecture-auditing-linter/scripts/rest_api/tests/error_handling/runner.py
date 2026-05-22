import sys
import os

# Add the root directory to sys.path to allow imports from scripts/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# Add global helpers path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
skills_dir = os.path.abspath(os.path.join(current_dir, '../../../../..'))
sys.path.append(skills_dir)

from rest_api.error_handling import ErrorHandling
from rest_api.tests.error_handling.cases import TEST_CASES

def run_tests():
    tool = ErrorHandling()
    passed = 0
    total = len(TEST_CASES)

    print(f"{'ID':<25} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 65)

    for case in TEST_CASES:
        actual_score, _ = tool.evaluate(None, case["code"])
        status = "✅ PASS" if abs(actual_score - case["expected_score"]) < 0.001 else "❌ FAIL"
        
        if status == "✅ PASS":
            passed += 1
            
        print(f"{case['id']:<25} | {case['expected_score']:<10.1f} | {actual_score:<10.4f} | {status}")
        if status == "❌ FAIL":
            print(f"   Reason: {case['description']}")

    print("-" * 65)
    print(f"Result: {passed}/{total} passed.")

if __name__ == "__main__":
    run_tests()
