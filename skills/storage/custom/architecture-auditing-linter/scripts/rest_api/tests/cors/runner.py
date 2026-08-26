import sys
import os

# Add the scripts directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
# Add global helpers path dynamically
current_dir = os.path.dirname(os.path.abspath(__file__))
skills_dir = os.path.abspath(os.path.join(current_dir, '../../../../..'))
sys.path.append(skills_dir)

from rest_api.cors import CorsImplementation
from cases import TEST_CASES


def run_tests():
    linter = CorsImplementation()
    passed = 0
    total = len(TEST_CASES)

    print(f"{'ID':<35} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 75)

    for case in TEST_CASES:
        actual_score, _ = linter.evaluate(None, case["code"])
        status = "✅ PASS" if abs(actual_score - case["expected_score"]) < 0.01 else "❌ FAIL"
        if status == "✅ PASS":
            passed += 1

        print(f"{case['id']:<35} | {case['expected_score']:<10.4f} | {actual_score:<10.4f} | {status}")
        if status == "❌ FAIL":
            print(f"   Reason: {case['description']}")

    print("-" * 75)
    print(f"Result: {passed}/{total} passed.")


if __name__ == "__main__":
    run_tests()
