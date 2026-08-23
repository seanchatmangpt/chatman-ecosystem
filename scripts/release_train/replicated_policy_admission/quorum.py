from collections import Counter
from dataclasses import dataclass
from .replica import ReplicaPolicyState
from .refusal import Refused
@dataclass(frozen=True)
class QuorumResult:
    generation:int; policy_digest:str|None; frontier_digest:str|None; agreeing:tuple[str,...]; split_brain:bool
def strict_majority(n:int)->int:
    if n<=0: raise Refused("EMPTY_REPLICA_SET")
    return n//2+1
def qualify_quorum(states:list[ReplicaPolicyState])->QuorumResult:
    if not states: raise Refused("EMPTY_REPLICA_SET")
    if len({s.replica_id for s in states})!=len(states): raise Refused("DUPLICATE_REPLICA")
    max_gen=max(s.generation for s in states); current=[s for s in states if s.generation==max_gen]
    counts=Counter((s.policy_digest,s.frontier_digest) for s in current); pair,count=max(counts.items(),key=lambda x:(x[1],x[0]))
    threshold=strict_majority(len(states)); divergent=len(counts)>1
    if count<threshold: return QuorumResult(max_gen,None,None,(),divergent)
    agreeing=tuple(sorted(s.replica_id for s in current if (s.policy_digest,s.frontier_digest)==pair))
    return QuorumResult(max_gen,pair[0],pair[1],agreeing,divergent and count==threshold and len(states)==2)
