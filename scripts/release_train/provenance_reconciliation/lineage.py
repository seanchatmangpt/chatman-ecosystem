from __future__ import annotations

from dataclasses import dataclass

from .model import Refused
from .provenance import EvidenceRecord


@dataclass(frozen=True)
class EvidenceEdge:
    predecessor: str
    successor: str


def order_evidence(records: list[EvidenceRecord], edges: list[EvidenceEdge]) -> list[str]:
    ids = {record.evidence_id for record in records}
    if len(ids) != len(records):
        raise Refused("DUPLICATE_EVIDENCE_ID")
    outgoing: dict[str, set[str]] = {item: set() for item in ids}
    indegree = {item: 0 for item in ids}
    for edge in edges:
        if edge.predecessor not in ids or edge.successor not in ids:
            raise Refused("EVIDENCE_EDGE_OUTSIDE_CLOSURE")
        if edge.predecessor == edge.successor:
            raise Refused("EVIDENCE_SELF_EDGE", edge.predecessor)
        if edge.successor not in outgoing[edge.predecessor]:
            outgoing[edge.predecessor].add(edge.successor)
            indegree[edge.successor] += 1
    ready = sorted(item for item, degree in indegree.items() if degree == 0)
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for nxt in sorted(outgoing[current]):
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
                ready.sort()
    if len(ordered) != len(ids):
        raise Refused("EVIDENCE_LINEAGE_CYCLE")
    return ordered
