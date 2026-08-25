from fractions import Fraction
from .refusal import Refused

def kaplan_meier(passages):
    rows = tuple(passages)
    if not rows:
        raise Refused("EMPTY_SURVIVAL_SAMPLE")
    survival = Fraction(1)
    curve = []
    for time in sorted({row.duration for row in rows}):
        at_risk = sum(1 for row in rows if row.duration >= time)
        events = sum(1 for row in rows if row.duration == time and row.event)
        censored = sum(1 for row in rows if row.duration == time and not row.event)
        if events:
            survival *= Fraction(at_risk - events, at_risk)
        curve.append((time, at_risk, events, censored, survival))
    return tuple(curve)

def on_time_probability(passages, deadline):
    survival = Fraction(1)
    for time, _, _, _, value in kaplan_meier(passages):
        if time <= deadline:
            survival = value
    return 1 - survival
