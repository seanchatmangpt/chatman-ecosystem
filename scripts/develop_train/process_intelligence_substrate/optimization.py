from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True, order=True)
class Candidate:
    name: str
    fitness: Fraction
    cost: Fraction
    latency: Fraction


def dominates(a: Candidate, b: Candidate) -> bool:
    weak = a.fitness >= b.fitness and a.cost <= b.cost and a.latency <= b.latency
    strict = a.fitness > b.fitness or a.cost < b.cost or a.latency < b.latency
    return weak and strict


def pareto(candidates: tuple[Candidate, ...]) -> tuple[Candidate, ...]:
    return tuple(sorted(c for c in candidates if not any(dominates(other, c) for other in candidates if other != c)))
