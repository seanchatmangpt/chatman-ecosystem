from __future__ import annotations

from dataclasses import dataclass
from collections import Counter

from .errors import Refused
from .subject import Subject


@dataclass(frozen=True)
class ReplicaVote:
    subject: Subject
    replica: str
    generation: int
    value_digest: str

    def __post_init__(self) -> None:
        if not self.replica.strip() or self.generation < 1 or len(self.value_digest) != 64:
            raise Refused("INVALID_REPLICA_VOTE")


def quorum_size(universe_size: int) -> int:
    if universe_size < 1:
        raise Refused("EMPTY_REPLICA_UNIVERSE")
    return universe_size // 2 + 1


@dataclass(frozen=True)
class QuorumResult:
    generation: int
    value_digest: str
    agreeing_replicas: tuple[str, ...]
    required: int


def strict_majority(subject: Subject, known_replicas: tuple[str, ...], votes: list[ReplicaVote]) -> QuorumResult | None:
    if len(set(known_replicas)) != len(known_replicas):
        raise Refused("INVALID_REPLICA_UNIVERSE")
    seen: set[str] = set()
    for vote in votes:
        if vote.subject != subject:
            raise Refused("FOREIGN_QUORUM_SUBJECT")
        if vote.replica not in known_replicas:
            raise Refused("FOREIGN_QUORUM_REPLICA")
        if vote.replica in seen:
            raise Refused("DUPLICATE_QUORUM_REPLICA")
        seen.add(vote.replica)
    counts = Counter((v.generation, v.value_digest) for v in votes)
    required = quorum_size(len(known_replicas))
    candidates = [key for key, count in counts.items() if count >= required]
    if len(candidates) > 1:
        raise Refused("MULTIPLE_STRICT_MAJORITY_VALUES")
    if not candidates:
        return None
    generation, digest = candidates[0]
    replicas = tuple(sorted(v.replica for v in votes if (v.generation, v.value_digest) == candidates[0]))
    return QuorumResult(generation, digest, replicas, required)
