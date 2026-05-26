import time

# ==========================================
# OpenEvolve - Initial Program Skeleton
# ==========================================
# This is the starting point for your evolutionary search.
# The LLM will use this as a reference to evolve better versions.

def process_data(input_data):
    """
    Core function that will be evolved by OpenEvolve.
    The evaluator expects this function to take a list of numbers
    and return their sum (as per the current skeleton/evaluator.py).
    
    Args:
        input_data (list): List of integers or floats.
        
    Returns:
        float/int: The sum of the input data.
    """
    # Simple baseline implementation
    if not input_data:
        return 0
    
    # Example logic: Summing all elements
    total = sum(input_data)
    
    # You can add some processing time to test the efficiency metric
    # time.sleep(0.01) 
    
    return total

if __name__ == "__main__":
    # Local testing
    example_input = [1, 2, 3, 4, 5]
    print(f"Input: {example_input}")
    print(f"Output: {process_data(example_input)}")
