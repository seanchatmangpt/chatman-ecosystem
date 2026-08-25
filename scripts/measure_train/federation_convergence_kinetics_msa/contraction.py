from fractions import Fraction

def total_variation(left, right):
    keys = set(left) | set(right)
    return sum((abs(left.get(key, Fraction(0)) - right.get(key, Fraction(0))) for key in keys), Fraction(0)) / 2

def dobrushin(kernel):
    rows = list(kernel.values())
    if len(rows) < 2:
        return Fraction(0)
    return max(total_variation(left, right) for index, left in enumerate(rows) for right in rows[index + 1:])
