import os
from evaluator import evaluate

def run_test():
    """
    Utility script to test whether your evaluator.py correctly scores your initial_program.py.
    ALWAYS run this before starting an OpenEvolve evolution. 
    If this fails, the LLM will fail too!
    """
    program_path = "initial_program.py"
    
    if not os.path.exists(program_path):
        print(f"Error: {program_path} not found.")
        return

    with open(program_path, "r") as f:
        code_string = f.read()

    print(f"Testing evaluator against {program_path}...\n")
    
    try:
        score, metadata = evaluate(code_string)
        print("✅ Evaluator ran successfully!")
        print(f"Score: {score}")
        print(f"Metadata: {metadata}")
        
        if not metadata.get("correct", False):
            print("⚠️ Warning: The initial program did not pass the correctness check.")
            print("This is fine if the initial program is supposed to be broken, but ensure the evaluator logic is sound.")
            
    except Exception as e:
        print(f"❌ Evaluator crashed: {str(e)}")

if __name__ == "__main__":
    run_test()
