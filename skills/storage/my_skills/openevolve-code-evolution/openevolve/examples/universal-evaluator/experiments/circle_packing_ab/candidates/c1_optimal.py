import json
import numpy as np


def construct_packing():
    n = 26
    centers = np.zeros((n, 2))
    centers[0] = [0.5, 0.5]
    for i in range(8):
        angle = 2 * np.pi * i / 8
        centers[i + 1] = [0.5 + 0.28 * np.cos(angle), 0.5 + 0.28 * np.sin(angle)]
    for i in range(16):
        angle = 2 * np.pi * i / 16
        centers[i + 9] = [0.5 + 0.65 * np.cos(angle), 0.5 + 0.65 * np.sin(angle)]
    centers[25] = [0.1, 0.1]
    centers = np.clip(centers, 0.05, 0.95)

    radii = np.ones(n)
    for i in range(n):
        x, y = centers[i]
        radii[i] = min(x, y, 1.0 - x, 1.0 - y)

    for i in range(n):
        for j in range(i + 1, n):
            dist = np.linalg.norm(centers[i] - centers[j])
            if radii[i] + radii[j] > dist:
                scale = dist / (radii[i] + radii[j])
                radii[i] *= scale
                radii[j] *= scale

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
