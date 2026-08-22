from __future__ import annotations
from dataclasses import dataclass
from .evidence import Evidence

@dataclass(frozen=True, order=True)
class ProcessEvent:
    event_id: str
    object_id: str
    activity: str
    timestamp: str
    attributes: tuple[tuple[str,str],...]

def project_ocel(rows: tuple[Evidence,...])->tuple[ProcessEvent,...]:
    events=[]
    for r in rows:
        events.append(ProcessEvent(f"evidence:{r.source_id}",r.subject.identity,f"observe:{r.kind}",r.observed_at.isoformat(),(("outcome",str(r.outcome)),("digest",r.digest))))
    return tuple(sorted(events))
