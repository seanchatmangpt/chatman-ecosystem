from dataclasses import dataclass
from .sensor import Sensor
from .refusals import Refused

@dataclass(frozen=True)
class IndependenceProof:
    left: str
    right: str
    proof_digest: str

    def pair(self):
        if self.left == self.right:
            raise Refused("SELF_INDEPENDENCE")
        return tuple(sorted((self.left, self.right)))

def admitted_pairs(sensors: list[Sensor], proofs: list[IndependenceProof]) -> set[tuple[str,str]]:
    by_id = {s.sensor_id:s for s in sensors}
    if len(by_id) != len(sensors):
        raise Refused("DUPLICATE_SENSOR")
    out=set()
    for proof in proofs:
        pair=proof.pair()
        if pair[0] not in by_id or pair[1] not in by_id or len(proof.proof_digest)!=64:
            raise Refused("INVALID_INDEPENDENCE_PROOF")
        a,b=(by_id[pair[0]],by_id[pair[1]])
        if a.family == b.family or a.domain == b.domain:
            raise Refused("CORRELATED_SENSOR_PAIR")
        out.add(pair)
    return out

def maximum_independent_subset(sensors: list[Sensor], pairs: set[tuple[str,str]]) -> tuple[str,...]:
    ids=sorted(s.sensor_id for s in sensors)
    best=()
    for mask in range(1,1<<len(ids)):
        cand=tuple(ids[i] for i in range(len(ids)) if mask & (1<<i))
        if all(tuple(sorted((cand[i],cand[j]))) in pairs for i in range(len(cand)) for j in range(i+1,len(cand))):
            if len(cand)>len(best) or (len(cand)==len(best) and cand<best): best=cand
    return best
