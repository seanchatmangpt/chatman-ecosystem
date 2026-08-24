from fractions import Fraction
from .refusal import Refused

def absorption_probability(kernel, start="ACTIVE", target="FIXED", horizon=10):
    if horizon < 0:
        raise Refused("INVALID_HORIZON")
    dist = {state: Fraction(int(state == start)) for state in kernel}
    for _ in range(horizon):
        nxt = {state: Fraction(0) for state in kernel}
        for source, probability in dist.items():
            for target_state, transition in kernel[source].items():
                nxt[target_state] += probability * transition
        dist = nxt
    return dist.get(target, Fraction(0))

def expected_hitting_steps(kernel, start="ACTIVE", target="FIXED", horizon=100):
    if horizon < 1:
        raise Refused("INVALID_HORIZON")
    dist = {state: Fraction(int(state == start)) for state in kernel}
    expected = Fraction(0)
    previous_hit = Fraction(0)
    for step in range(1, horizon + 1):
        nxt = {state: Fraction(0) for state in kernel}
        for source, probability in dist.items():
            for target_state, transition in kernel[source].items():
                nxt[target_state] += probability * transition
        hit = nxt.get(target, Fraction(0))
        newly = max(Fraction(0), hit - previous_hit)
        expected += step * newly
        previous_hit = hit
        dist = nxt
    return expected, 1 - previous_hit
