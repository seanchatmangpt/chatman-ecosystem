from math import sqrt

def wilson_upper(errors: int, total: int, z: float = 1.959963984540054) -> float:
    if total <= 0:
        raise ValueError("total must be positive")
    p = errors / total
    z2 = z * z
    denom = 1.0 + z2 / total
    center = p + z2 / (2.0 * total)
    radius = z * sqrt((p * (1.0 - p) + z2 / (4.0 * total)) / total)
    return min(1.0, (center + radius) / denom)
