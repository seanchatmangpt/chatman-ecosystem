from fractions import Fraction

def resolved_fraction(observations):
    rows = tuple(observations)
    return Fraction(sum(row.state == "RESOLVED" for row in rows), len(rows)) if rows else Fraction(0)

def censoring_fraction(observations):
    rows = tuple(observations)
    return Fraction(sum(row.state != "RESOLVED" for row in rows), len(rows)) if rows else Fraction(0)
