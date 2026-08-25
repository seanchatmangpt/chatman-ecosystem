from fractions import Fraction
from .refusal import Refused

def nelson_aalen(passages):
    rows = tuple(passages)
    if not rows:
        raise Refused("EMPTY_HAZARD_SAMPLE")
    cumulative = Fraction(0)
    curve = []
    for time in sorted({row.duration for row in rows}):
        at_risk = sum(1 for row in rows if row.duration >= time)
        events = sum(1 for row in rows if row.duration == time and row.event)
        if events:
            cumulative += Fraction(events, at_risk)
        curve.append((time, at_risk, events, cumulative))
    return tuple(curve)
