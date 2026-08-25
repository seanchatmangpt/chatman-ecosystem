import math

def wilson(successes, total, z=1.96):
    if total <= 0:
        return (0.0, 1.0)
    p = successes / total
    z2 = z * z
    den = 1 + z2 / total
    center = (p + z2 / (2 * total)) / den
    margin = z * math.sqrt((p * (1 - p) + z2 / (4 * total)) / total) / den
    return max(0.0, center - margin), min(1.0, center + margin)
