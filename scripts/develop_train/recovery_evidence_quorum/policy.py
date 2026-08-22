from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence import RecoveryWitness, WitnessOutcome
from .subject import Refused


class Standing(str, Enum):
    UNKNOWN = "UNKNOWN"
    PARTIAL_ALIVE = "PARTIAL_ALIVE"
    BUILD_BROKEN = "BUILD_BROKEN"
    BLOCKED = "BLOCKED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class QuorumPolicy:
    min_independent_clusters: int = 2
    required_scopes: frozenset[str] = frozenset({"recovery"})

    def __post_init__(self) -> None:
        if self.min_independent_clusters < 1 or not self.required_scopes:
            raise Refused("REFUSED[INVALID_QUORUM_POLICY]")


def evaluate_quorum(policy: QuorumPolicy, witnesses: tuple[RecoveryWitness, ...], clusters: tuple[tuple[str, ...], ...]) -> Standing:
    if any(w.outcome is WitnessOutcome.FAIL for w in witnesses):
        return Standing.BUILD_BROKEN
    if any(w.outcome is WitnessOutcome.UNSUPPORTED for w in witnesses):
        return Standing.UNSUPPORTED
    if any(w.outcome in {WitnessOutcome.PENDING, WitnessOutcome.UNKNOWN} for w in witnesses):
        return Standing.UNKNOWN
    by_id = {w.evidence_id: w for w in witnesses}
    qualifying = 0
    scopes: set[str] = set()
    for cluster in clusters:
        members = [by_id[item] for item in cluster]
        if members and all(m.outcome is WitnessOutcome.PASS for m in members):
            qualifying += 1
            scopes.update(m.scope for m in members)
    if not policy.required_scopes.issubset(scopes) or qualifying < policy.min_independent_clusters:
        return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE
