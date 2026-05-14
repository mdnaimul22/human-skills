import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))

from rest_api.auth import AuthImplementation
from cases import TEST_CASES

def run_tests():
    linter = AuthImplementation()
    passed = 0
    print(f"{'ID':<35} | {'Expected':<10} | {'Actual':<10} | {'Status'}")
    print("-" * 75)
    for case in TEST_CASES:
        actual = linter.evaluate(None, case["code"])
        status = "✅ PASS" if abs(actual - case["expected_score"]) < 0.01 else "❌ FAIL"
        if status == "✅ PASS": passed += 1
        print(f"{case['id']:<35} | {case['expected_score']:<10.4f} | {actual:<10.4f} | {status}")
    print("-" * 75)
    print(f"Result: {passed}/{len(TEST_CASES)} passed.\\n")

if __name__ == "__main__":
    run_tests()
