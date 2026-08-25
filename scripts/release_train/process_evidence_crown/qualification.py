from dataclasses import dataclass
from .subject import Subject
from .graph import EvidenceGraph
from .evidence import Outcome
from .currentness import current_frontier
from .methodology import require_methodologies
from .rails import require_rails
from .failures import require_failure_worlds
from .standing import Standing,combine
from .receipt import Receipt
from .refusal import Refused
@dataclass(frozen=True)
class Qualification:
    standing:Standing; receipt:Receipt|None; blockers:tuple[str,...]

def qualify(subject:Subject,generation:int,graph:EvidenceGraph,methodologies,rails,failures,parent_digests=()):
    if any(n.subject!=subject for n in graph.nodes.values()): raise Refused('FOREIGN_EVIDENCE_SUBJECT')
    current_frontier(list(graph.nodes.values())); require_methodologies(methodologies); require_rails(rails); require_failure_worlds(failures)
    failed=tuple(sorted(n.id for n in graph.nodes.values() if n.outcome==Outcome.FAIL))
    if failed: return Qualification(Standing.BUILD_BROKEN,None,failed)
    states=[]
    for n in graph.nodes.values(): states.append(Standing.UNKNOWN if n.outcome==Outcome.UNKNOWN else Standing.UNSUPPORTED if n.outcome==Outcome.UNSUPPORTED else Standing.PARTIAL_ALIVE)
    standing=combine(states)
    if standing!=Standing.PARTIAL_ALIVE: return Qualification(standing,None,())
    r=Receipt(subject,generation,standing.value,tuple(graph.order()),tuple(parent_digests))
    return Qualification(standing,r,())
