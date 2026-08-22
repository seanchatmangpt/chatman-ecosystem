from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence import RecoveryWitness
from .provenance import ProvenanceGraph


class EvidenceRelation(str, Enum):
    SAME_EVIDENCE = "SAME_EVIDENCE"
    CORRELATED = "CORRELATED"
    INDEPENDENT = "INDEPENDENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class IndependenceEvidence:
    left_id: str
    right_id: str
    proof_digest: str

    def pair(self) -> frozenset[str]:
        return frozenset((self.left_id, self.right_id))


def relation(left: RecoveryWitness, right: RecoveryWitness, graph: ProvenanceGraph, admitted: tuple[IndependenceEvidence, ...] = ()) -> EvidenceRelation:
    if left.evidence_id == right.evidence_id or left.source.fingerprint == right.source.fingerprint:
        return EvidenceRelation.SAME_EVIDENCE
    pair = frozenset((left.evidence_id, right.evidence_id))
    if any(item.pair() == pair and len(item.proof_digest) == 64 for item in admitted):
        return EvidenceRelation.INDEPENDENT
    if graph.derives_from(left.evidence_id, right.evidence_id) or graph.derives_from(right.evidence_id, left.evidence_id):
        return EvidenceRelation.CORRELATED
    a, b = left.source, right.source
    if a.producer == b.producer or a.run_id == b.run_id or a.artifact_digest == b.artifact_digest or a.family == b.family:
        return EvidenceRelation.CORRELATED
    return EvidenceRelation.UNKNOWN


def correlated_clusters(witnesses: tuple[RecoveryWitness, ...], graph: ProvenanceGraph, admitted: tuple[IndependenceEvidence, ...] = ()) -> tuple[tuple[str, ...], ...]:
    ids = [w.evidence_id for w in witnesses]
    parent = {value: value for value in ids}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    by_id = {w.evidence_id: w for w in witnesses}
    for i, left_id in enumerate(ids):
        for right_id in ids[i + 1:]:
            rel = relation(by_id[left_id], by_id[right_id], graph, admitted)
            if rel in {EvidenceRelation.SAME_EVIDENCE, EvidenceRelation.CORRELATED}:
                union(left_id, right_id)
    groups: dict[str, list[str]] = {}
    for value in ids:
        groups.setdefault(find(value), []).append(value)
    return tuple(sorted((tuple(sorted(group)) for group in groups.values()), key=lambda x: x[0]))
