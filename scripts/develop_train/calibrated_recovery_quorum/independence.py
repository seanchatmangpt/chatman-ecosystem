from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence_source import EvidenceSource


class Relation(str, Enum):
    SAME = "SAME_EVIDENCE"
    CORRELATED = "CORRELATED"
    INDEPENDENT = "INDEPENDENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class IndependenceProof:
    left: str
    right: str
    proof_digest: str

    def __post_init__(self) -> None:
        if self.left == self.right or len(self.proof_digest) != 64:
            raise ValueError("REFUSED[INVALID_INDEPENDENCE_PROOF]")


def relation(
    a: EvidenceSource,
    b: EvidenceSource,
    proofs: tuple[IndependenceProof, ...] = (),
) -> Relation:
    if a.fingerprint == b.fingerprint:
        return Relation.SAME
    key = frozenset((a.fingerprint, b.fingerprint))
    if any(frozenset((p.left, p.right)) == key for p in proofs):
        return Relation.INDEPENDENT
    if (
        a.producer == b.producer
        or a.run_id == b.run_id
        or a.artifact_id == b.artifact_id
        or a.family == b.family
    ):
        return Relation.CORRELATED
    return Relation.UNKNOWN


def correlated_clusters(
    sources: tuple[EvidenceSource, ...],
    proofs: tuple[IndependenceProof, ...] = (),
) -> tuple[tuple[str, ...], ...]:
    parent = {s.fingerprint: s.fingerprint for s in sources}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for i, left in enumerate(sources):
        for right in sources[i + 1 :]:
            if relation(left, right, proofs) in {Relation.SAME, Relation.CORRELATED}:
                union(left.fingerprint, right.fingerprint)
    groups: dict[str, list[str]] = {}
    for source in sources:
        groups.setdefault(find(source.fingerprint), []).append(source.fingerprint)
    return tuple(sorted((tuple(sorted(v)) for v in groups.values()), key=lambda group: group[0]))
