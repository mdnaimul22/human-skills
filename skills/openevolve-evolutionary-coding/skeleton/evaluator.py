import time
import random
from typing import Dict, Any, Tuple

def evaluate(code_string: str) -> Tuple[float, Dict[str, Any]]:
    """
    Evaluates the LLM generated code.
    Must return a tuple: (score, metadata_dict)
    Higher score is better.
    """
    metadata = {"correct": False, "execution_time": None, "error": None}
    
    # 1. Safely load the generated code
    namespace = {}
    try:
        exec(code_string, namespace)
        if "process_data" not in namespace:
            raise ValueError("Function 'process_data' not found in generated code.")
        process_data = namespace["process_data"]
    except Exception as e:
        metadata["error"] = f"Compilation Error: {str(e)}"
        return 0.0, metadata

    # 2. Test Data Generation
    test_data = [random.randint(0, 1000) for _ in range(500)]
    expected_output = sorted(test_data)

    # 3. Execution & Correctness Check
    start_time = time.time()
    try:
        # Pass a copy to prevent in-place modification cheating if expected
        actual_output = process_data(test_data.copy()) 
        execution_time = time.time() - start_time
        
        if actual_output != expected_output:
            metadata["error"] = "Output did not match expected sorted list."
            return 0.0, metadata
            
        metadata["correct"] = True
        metadata["execution_time"] = execution_time
        
    except Exception as e:
        metadata["error"] = f"Runtime Error: {str(e)}"
        return 0.0, metadata

    # 4. Scoring Logic (Faster execution = higher score)
    # Using inverse time so smaller time gives bigger score.
    # Cap the max score to prevent infinity if time is near 0.
    base_score = 100.0
    time_penalty = execution_time * 1000  # Penalize based on ms 
    final_score = max(1.0, base_score - time_penalty)
    
    return final_score, metadata
