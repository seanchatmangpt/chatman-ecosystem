from collections import defaultdict
from .evidence import EvidenceNode
from .refusal import Refused

def current_frontier(nodes: list[EvidenceNode]):
    by={}; groups=defaultdict(list)
    for n in nodes: groups[(n.kind,n.domain)].append(n)
    for key,items in groups.items():
        g=max(x.generation for x in items); latest=[x for x in items if x.generation==g]
        identities={(x.implementation,x.model,x.outcome,x.confidence) for x in latest}
        if len(identities)>1: raise Refused("DIVERGENT_CURRENT_EVIDENCE", str(key))
        by[key]=latest[0]
    return by

def require_generation(node: EvidenceNode, generation: int):
    if node.generation!=generation: raise Refused("STALE_EVIDENCE_GENERATION", node.id)
    return node
