from __future__ import annotations
from fractions import Fraction

def score(observed: tuple[str, ...], expected: tuple[str, ...]) -> Fraction:
    if not expected:
        return Fraction(1 if not observed else 0, 1)
    matched = sum(1 for a, b in zip(observed, expected) if a == b)
    penalty = abs(len(observed) - len(expected))
    numerator = max(0, matched - penalty)
    return Fraction(numerator, len(expected))
