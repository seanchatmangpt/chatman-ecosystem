from enum import Enum
from .evidence import EvidenceSource, RecoveryWitness

class Relation(str, Enum):
    SAME='SAME_EVIDENCE'; CORRELATED='CORRELATED'; INDEPENDENT='INDEPENDENT'; UNKNOWN='UNKNOWN'

def relation(left: EvidenceSource, right: EvidenceSource, explicit_pairs: set[frozenset[str]]|None=None) -> Relation:
    if left.fingerprint==right.fingerprint: return Relation.SAME
    if explicit_pairs and frozenset((left.fingerprint,right.fingerprint)) in explicit_pairs: return Relation.INDEPENDENT
    if left.producer==right.producer or left.run_id==right.run_id or left.artifact_id==right.artifact_id or left.family==right.family: return Relation.CORRELATED
    return Relation.UNKNOWN

def clusters(witnesses: list[RecoveryWitness], explicit_pairs: set[frozenset[str]]|None=None) -> list[tuple[RecoveryWitness,...]]:
    groups=[]
    for witness in sorted(witnesses,key=lambda w:w.source.fingerprint):
        placed=False
        for group in groups:
            if any(relation(witness.source,other.source,explicit_pairs) in {Relation.SAME,Relation.CORRELATED} for other in group):
                group.append(witness); placed=True; break
        if not placed: groups.append([witness])
    return [tuple(group) for group in groups]
