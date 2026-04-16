# initial_program.py
# -------------------------------------------------------------------------------------
# This is the starting baseline code that the OpenEvolve LLM will attempt to improve.
# Replace the logic here with the problem you want the LLM to solve.
# -------------------------------------------------------------------------------------

def process_data(data: list) -> list:
    """
    Dummy Example: A highly inefficient list sorting function.
    The LLM's goal will be to optimize this algorithm for speed and correctness.
    """
    if len(data) <= 1:
        return data
        
    result = []
    # Intentionally bad algorithm to give the LLM room for improvement
    while data:
        minimum = data[0]
        for x in data:
            if x < minimum:
                minimum = x
        result.append(minimum)
        data.remove(minimum)
        
    return result
