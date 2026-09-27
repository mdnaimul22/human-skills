from main import sort_numbers
def test_basic(): assert sort_numbers([3,1,2]) == [1,2,3]
def test_duplicates(): assert sort_numbers([2,1,2,1]) == [1,1,2,2]
def test_empty(): assert sort_numbers([]) == []
def test_negative(): assert sort_numbers([3,-1,0,-5]) == [-5,-1,0,3]
