import os
import sys
import json
from evaluator import evaluate

def run_test():
    """
    Validation script for the OpenEvolve skeleton.
    Verifies that evaluator.py can correctly load and score initial_program.py.
    """
    # Use absolute paths to avoid confusion
    current_dir = os.path.dirname(os.path.abspath(__file__))
    program_path = os.path.join(current_dir, "initial_program.py")
    
    print("=" * 50)
    print("🛡️  OPENEVOLVE EVALUATOR VALIDATION")
    print("=" * 50)
    
    if not os.path.exists(program_path):
        print(f"❌ Error: {program_path} not found.")
        return

    print(f"[*] Testing evaluator against: {os.path.basename(program_path)}")
    
    try:
        # Run the evaluation
        result = evaluate(program_path)
        
        # Accessing metrics and artifacts from EvaluationResult
        metrics = result.metrics
        artifacts = result.artifacts
        
        print("\n📊 METRICS:")
        for key, value in metrics.items():
            print(f"  - {key}: {value}")
            
        print("\n🎨 ARTIFACTS:")
        # Pretty print artifacts if they contain complex data
        print(json.dumps(artifacts, indent=2))
        
        # Validation Logic
        print("\n" + "=" * 50)
        if metrics.get("combined_score", 0) > 0:
            print("✅ SUCCESS: Evaluator is working and produced a positive fitness score.")
        else:
            print("⚠️ WARNING: Evaluator returned a score of 0.0.")
            print("Check if initial_program.py logic matches the test cases in evaluator.py.")
            
        if artifacts.get("error_type"):
            print(f"❌ ERROR DETECTED: {artifacts['error_type']} - {artifacts['error_message']}")
            if artifacts.get("suggestion"):
                print(f"💡 SUGGESTION: {artifacts['suggestion']}")
        
    except Exception as e:
        print(f"\n❌ CRITICAL FAILURE: The evaluator script itself crashed.")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    print("=" * 50)

if __name__ == "__main__":
    run_test()
