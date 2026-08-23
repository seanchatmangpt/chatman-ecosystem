from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from .causality import VectorClock, concurrent_pairs
from .quorum import QuorumResult, ReplicaVote


class Topology(str, Enum):
    HEALTHY = "HEALTHY"
    PARTIAL_VISIBILITY = "PARTIAL_VISIBILITY"
    SPLIT_BRAIN = "SPLIT_BRAIN"
    STALE_MAJORITY = "STALE_MAJORITY"
    NO_QUORUM = "NO_QUORUM"


@dataclass(frozen=True)
class TopologyResult:
    topology: Topology
    concurrency_pairs: int


def classify(
    votes: list[ReplicaVote],
    quorum: QuorumResult | None,
    clocks: dict[str, VectorClock],
    coverage: Fraction,
) -> TopologyResult:
    concurrency = concurrent_pairs(clocks) if clocks else 0
    if quorum is None:
        same_generation_values: dict[int, set[str]] = {}
        for vote in votes:
            same_generation_values.setdefault(vote.generation, set()).add(vote.value_digest)
        if any(len(values) > 1 for values in same_generation_values.values()) and concurrency:
            return TopologyResult(Topology.SPLIT_BRAIN, concurrency)
        return TopologyResult(Topology.NO_QUORUM, concurrency)
    newest_generation = max(v.generation for v in votes)
    if quorum.generation < newest_generation:
        return TopologyResult(Topology.STALE_MAJORITY, concurrency)
    if coverage < 1:
        return TopologyResult(Topology.PARTIAL_VISIBILITY, concurrency)
    if concurrency:
        return TopologyResult(Topology.SPLIT_BRAIN, concurrency)
    return TopologyResult(Topology.HEALTHY, 0)
