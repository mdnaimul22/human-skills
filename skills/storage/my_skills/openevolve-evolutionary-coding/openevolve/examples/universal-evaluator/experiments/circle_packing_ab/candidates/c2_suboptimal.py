import json
import numpy as np


def construct_packing():
    n = 26
    centers = np.zeros((n, 2))
    for i in range(n):
        centers[i] = [0.05 + 0.035 * i, 0.05 + 0.035 * i]
    radii = np.full(n, 0.012)
    sum_radii = float(np.sum(radii))
    return centers, radii, sum_radii


def run_packing():
    return construct_packing()


if __name__ == "__main__":
    centers, radii, sum_radii = run_packing()
    print(json.dumps({
        "centers": centers.tolist(),
        "radii": radii.tolist(),
        "sum_radii": sum_radii,
    }))
