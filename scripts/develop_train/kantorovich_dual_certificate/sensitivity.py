from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Sensitivity:
    max_slope: Fraction
    breakdown_radius: Fraction | None

def analyze(points, bound):
    points = sorted((Fraction(radius), Fraction(value)) for radius, value in points)
    if len(points) < 2:
        raise Refused("INSUFFICIENT_SENSITIVITY_POINTS")
    slopes = []
    for (r0, v0), (r1, v1) in zip(points, points[1:]):
        if r1 <= r0:
            raise Refused("NONINCREASING_RADIUS")
        if v1 < v0:
            raise Refused("NON_MONOTONE_ROBUST_OBJECTIVE")
        slopes.append((v1 - v0) / (r1 - r0))
    breakdown = next((radius for radius, value in points if value > Fraction(bound)), None)
    return Sensitivity(max(slopes), breakdown)
