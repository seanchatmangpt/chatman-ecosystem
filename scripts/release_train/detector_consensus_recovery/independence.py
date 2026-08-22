from dataclasses import dataclass
from itertools import combinations

@dataclass(frozen=True)
class IndependenceProof:
    left: str
    right: str
    independent: bool
    basis: str
    def pair(self):
        if self.left==self.right: raise ValueError("REFUSED[SELF_INDEPENDENCE]")
        return tuple(sorted((self.left,self.right)))

def independent_clique(detectors, proofs):
    names=sorted(set(detectors)); edges={p.pair() for p in proofs if p.independent and p.basis}; best=[]
    for size in range(1,len(names)+1):
        for combo in combinations(names,size):
            if all(tuple(sorted((a,b))) in edges for a,b in combinations(combo,2)) and len(combo)>len(best): best=list(combo)
    return tuple(best)
