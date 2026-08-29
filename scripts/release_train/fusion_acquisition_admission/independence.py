from dataclasses import dataclass
from itertools import combinations
from .errors import Refused
from .sensor import SensorIdentity

@dataclass(frozen=True)
class IndependenceProof:
    left: SensorIdentity
    right: SensorIdentity
    proof_id: str
    def __post_init__(self):
        if self.left == self.right:
            raise Refused("SELF_INDEPENDENCE")
        if self.left.subject != self.right.subject:
            raise Refused("CROSS_SUBJECT_INDEPENDENCE")
        if self.left.family == self.right.family or self.left.domain == self.right.domain:
            raise Refused("CORRELATION_LAUNDERING")
        if not self.proof_id:
            raise Refused("MISSING_INDEPENDENCE_PROOF")
    def pair(self):
        return frozenset((self.left.sensor_id, self.right.sensor_id))

def admitted_pairs(proofs):
    pairs=set()
    for proof in proofs:
        pair=proof.pair()
        if pair in pairs:
            raise Refused("DUPLICATE_INDEPENDENCE_PROOF")
        pairs.add(pair)
    return pairs

def maximum_independent_subset(sensors, proofs):
    ids=sorted({s.sensor_id for s in sensors})
    if len(ids) != len(sensors):
        raise Refused("DUPLICATE_SENSOR")
    pairs=admitted_pairs(proofs)
    for size in range(len(ids), 0, -1):
        for candidate in combinations(ids, size):
            if all(frozenset(pair) in pairs for pair in combinations(candidate, 2)):
                return candidate
    return tuple()
