from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .evidence import Evidence

class Refusal(ValueError):
    pass

@dataclass(frozen=True)
class Supersession:
    older_id: str
    newer_id: str
    reason: str

ALLOWED_REASONS = {"NEW_HEAD", "NEW_RUN", "NEW_ARTIFACT", "NEW_RECEIPT", "CORRECTION"}

def validate_relations(evidence: Iterable[Evidence], relations: Iterable[Supersession]) -> tuple[Supersession, ...]:
    by_id = {e.evidence_id: e for e in evidence}
    edges: dict[str, str] = {}
    result=[]
    for rel in relations:
        if rel.reason not in ALLOWED_REASONS:
            raise Refusal("REFUSED[UNKNOWN_SUPERSESSION_REASON]")
        if rel.older_id not in by_id or rel.newer_id not in by_id:
            raise Refusal("REFUSED[ORPHAN_SUPERSESSION]")
        old, new = by_id[rel.older_id], by_id[rel.newer_id]
        if old.subject.repo != new.subject.repo or old.scope != new.scope:
            raise Refusal("REFUSED[INCOMPATIBLE_SUPERSESSION]")
        if not old.observed_at < new.observed_at:
            raise Refusal("REFUSED[NON_FORWARD_SUPERSESSION]")
        edges[rel.older_id] = rel.newer_id
        result.append(rel)
    for start in edges:
        seen=set(); cur=start
        while cur in edges:
            if cur in seen:
                raise Refusal("REFUSED[SUPERSESSION_CYCLE]")
            seen.add(cur); cur=edges[cur]
    return tuple(result)
