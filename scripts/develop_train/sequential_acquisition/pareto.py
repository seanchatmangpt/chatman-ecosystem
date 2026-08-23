from .policy import Candidate

def dominates(a: Candidate, b: Candidate) -> bool:
    no_worse = (a.predicted_information_bits >= b.predicted_information_bits and a.independence_gain >= b.independence_gain and a.cost <= b.cost and a.latency <= b.latency)
    strict = (a.predicted_information_bits > b.predicted_information_bits or a.independence_gain > b.independence_gain or a.cost < b.cost or a.latency < b.latency)
    return no_worse and strict

def frontier(candidates: list[Candidate]) -> list[Candidate]:
    return sorted([c for c in candidates if not any(dominates(other, c) for other in candidates if other != c)], key=lambda c: c.candidate_id)
