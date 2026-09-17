import numpy as np
from scipy.stats import kendalltau

def kendall_tau_score(predicted: np.ndarray, ground_truth: np.ndarray) -> float:
    p = np.asarray(predicted, dtype=float)
    g = np.asarray(ground_truth, dtype=float)
    if len(p) < 2:
        return 0.0
    if np.all(p == p[0]) or np.all(g == g[0]):
        return 0.0
    tau, _ = kendalltau(p, g)
    if not np.isfinite(tau):
        return 0.0
    return float(tau)

def discordance_rate(predicted: np.ndarray, ground_truth: np.ndarray) -> float:
    p = np.asarray(predicted, dtype=float)
    g = np.asarray(ground_truth, dtype=float)
    n = len(p)
    if n < 2:
        return 0.0
    discordant = 0
    total = 0
    for i in range(n):
        for j in range(i + 1, n):
            dp = p[i] - p[j]
            dg = g[i] - g[j]
            if dp == 0 or dg == 0:
                continue
            total += 1
            if dp * dg < 0:
                discordant += 1
    return float(discordant / total) if total > 0 else 0.0
