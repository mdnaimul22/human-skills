import sys
import os

# Add global helpers path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
skills_dir = os.path.abspath(os.path.join(current_dir, '../../../../..'))
scripts_dir = os.path.abspath(os.path.join(current_dir, '../../..'))
sys.path.append(skills_dir)
sys.path.append(scripts_dir)

from rest_api.status_code import StatusCodeUsage
from cases import TEST_CASES

def run_tests():
    tool = StatusCodeUsage()
    passed = 0
    total = len(TEST_CASES)

    print(f"{'ID':<25} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 65)

    for case in TEST_CASES:
        actual_score = tool.evaluate(None, case["code"])
        status = "✅ PASS" if abs(actual_score - case["expected_score"]) < 0.001 else "❌ FAIL"
        
        if status == "✅ PASS":
            passed += 1
            
        print(f"{case['id']:<25} | {case['expected_score']:<10.4f} | {actual_score:<10.4f} | {status}")
        if status == "❌ FAIL":
            print(f"   Reason: {case['description']}")

    print("-" * 65)
    print(f"Result: {passed}/{total} passed.")

if __name__ == "__main__":
    run_tests()
