from dataclasses import dataclass
from .graph import DependencyGraph

REASONS={
 'NEW_HEAD':'SUPERSEDED_SUBJECT','NEW_RECEIPT':'SUPERSEDED_RECEIPT','SCHEMA_CHANGE':'SCHEMA_DRIFT',
 'EXPIRED':'LEASE_EXPIRED','BUILD_BROKEN':'PRODUCER_BUILD_BROKEN','BLOCKED':'PRODUCER_BLOCKED','RECOVERED':'PRODUCER_RECOVERED_REQUALIFY'
}

@dataclass(frozen=True)
class Impact:
    subject: str
    depth: int
    reason: str

def build_cascade(bindings,event):
    graph=DependencyGraph(bindings)
    reason=REASONS[event.kind]
    return tuple(Impact(subject=s,depth=d,reason=reason) for s,d in graph.descendants(event.producer.key))
