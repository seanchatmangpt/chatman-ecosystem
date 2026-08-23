import math
from fractions import Fraction

def closure_fraction(census):
    required = [row for row in census if row[2]]
    if not required:
        return Fraction(1)
    passed = sum(1 for row in required if row[3] == "PASS")
    return Fraction(passed, len(required))

def state_entropy(census):
    required = [row for row in census if row[2]]
    if not required:
        return 0.0
    counts = {}
    for row in required:
        counts[row[3]] = counts.get(row[3], 0) + 1
    total = len(required)
    return -sum((n/total) * math.log2(n/total) for n in counts.values())

def realized_closure_gain(before_census, after_census):
    return closure_fraction(after_census) - closure_fraction(before_census)
