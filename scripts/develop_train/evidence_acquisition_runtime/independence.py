from dataclasses import dataclass
from itertools import combinations
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class IndependenceProof:
    left:str; right:str; proof_digest:str
    def __post_init__(self):
        if self.left==self.right or len(self.proof_digest)!=64: raise Refusal('REFUSED_INVALID_INDEPENDENCE_PROOF')
def admitted_pairs(candidates,proofs):
    known={c.candidate_id:c for c in candidates}; out=set()
    for p in proofs:
        if p.left not in known or p.right not in known: raise Refusal('REFUSED_FOREIGN_INDEPENDENCE_PROOF')
        a,b=known[p.left],known[p.right]
        if a.family!=b.family and a.domain!=b.domain: out.add(frozenset((p.left,p.right)))
    return out
def pairwise_independent(ids,pairs): return all(frozenset(x) in pairs for x in combinations(ids,2))
