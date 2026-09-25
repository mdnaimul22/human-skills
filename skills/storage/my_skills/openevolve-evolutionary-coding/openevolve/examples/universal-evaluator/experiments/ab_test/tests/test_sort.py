import random
from main import sort_numbers


def test_basic():
    assert sort_numbers([3, 1, 2]) == [1, 2, 3]


def test_duplicates():
    assert sort_numbers([2, 1, 2, 1]) == [1, 1, 2, 2]


def test_empty():
    assert sort_numbers([]) == []


def test_negative():
    assert sort_numbers([3, -1, 0, -5]) == [-5, -1, 0, 3]


def test_large():
    rnd = random.Random(42)
    sample = [rnd.randint(-1000, 1000) for _ in range(1000)]
    assert sort_numbers(sample) == sorted(sample)
