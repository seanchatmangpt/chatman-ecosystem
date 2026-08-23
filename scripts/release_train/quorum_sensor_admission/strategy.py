from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .topology import Topology, TopologyResult


class Strategy(str, Enum):
    STRICT_CURRENT = "STRICT_CURRENT"
    MAX_COVERAGE = "MAX_COVERAGE"
    MIN_AMBIGUITY = "MIN_AMBIGUITY"


@dataclass(frozen=True)
class StrategyScore:
    strategy: Strategy
    admitted: bool
    score: tuple[int, int, int]


def score_strategies(topology: TopologyResult, coverage: Fraction, lag_seconds: int) -> tuple[StrategyScore, ...]:
    healthy = topology.topology == Topology.HEALTHY
    no_split = topology.topology not in {Topology.SPLIT_BRAIN, Topology.STALE_MAJORITY}
    return (
        StrategyScore(Strategy.STRICT_CURRENT, healthy, (int(healthy), coverage.numerator * 1000 // coverage.denominator, -lag_seconds)),
        StrategyScore(Strategy.MAX_COVERAGE, no_split and coverage >= Fraction(2, 3), (coverage.numerator * 1000 // coverage.denominator, -topology.concurrency_pairs, -lag_seconds)),
        StrategyScore(Strategy.MIN_AMBIGUITY, no_split, (-topology.concurrency_pairs, coverage.numerator * 1000 // coverage.denominator, -lag_seconds)),
    )


def select(scores: tuple[StrategyScore, ...]) -> Strategy | None:
    admitted = [item for item in scores if item.admitted]
    if not admitted:
        return None
    return max(admitted, key=lambda item: (item.score, item.strategy.value)).strategy
