def sort_numbers(values: list[int]) -> list[int]:
    arr = list(values)
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr


if __name__ == "__main__":
    print(sort_numbers([5, 1, 4, 2, 3]))
