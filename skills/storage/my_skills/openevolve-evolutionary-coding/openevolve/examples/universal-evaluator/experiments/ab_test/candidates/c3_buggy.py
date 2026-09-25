def sort_numbers(values: list[int]) -> list[int]:
    if not values:
        raise IndexError("empty list not supported")
    return list(set(values))


if __name__ == "__main__":
    print(sort_numbers([5, 1, 4, 2, 3]))
