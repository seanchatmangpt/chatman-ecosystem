from fractions import Fraction
from .refusal import Refused

EVENTS = {"FIXED", "REGRESSED", "BLOCKED"}

def cumulative_incidence(episodes):
    rows = tuple(episodes)
    if not rows:
        raise Refused("EMPTY_COMPETING_RISK_SAMPLE")
    survival = Fraction(1)
    incidence = {event: Fraction(0) for event in EVENTS}
    out = []
    for time in sorted({episode.duration for episode in rows}):
        at_risk = sum(1 for episode in rows if episode.duration >= time)
        counts = {event: sum(1 for episode in rows if episode.duration == time and episode.terminal_state == event) for event in EVENTS}
        for event, count in counts.items():
            if count:
                incidence[event] += survival * Fraction(count, at_risk)
        all_events = sum(counts.values())
        if all_events:
            survival *= Fraction(at_risk - all_events, at_risk)
        out.append((time, survival, tuple((event, incidence[event]) for event in sorted(EVENTS))))
    return tuple(out)
