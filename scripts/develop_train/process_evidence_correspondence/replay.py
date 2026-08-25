import hashlib, json
from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class ReplayNode:
    node_id:str; body_digest:str; parents:tuple[str,...]=()
def replay_root(nodes):
    nodes=list(nodes); d={n.node_id:n for n in nodes}
    if len(d)!=len(nodes): raise Refused("DUPLICATE_REPLAY_NODE")
    done={}; pending=set(d)
    while pending:
        ready=sorted(k for k in pending if all(p in done for p in d[k].parents))
        if not ready: raise Refused("REPLAY_DAG_CYCLE_OR_MISSING_PARENT")
        for k in ready:
            n=d[k]; payload={"node_id":k,"body_digest":n.body_digest,"parents":[done[p] for p in sorted(n.parents)]}
            done[k]=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest(); pending.remove(k)
    roots=[done[k] for k in d if not any(k in n.parents for n in d.values())]
    return hashlib.sha256("".join(sorted(roots)).encode()).hexdigest()
