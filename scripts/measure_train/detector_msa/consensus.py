from dataclasses import dataclass
from itertools import combinations
from .subject import Refused

@dataclass(frozen=True, order=True)
class DetectorVote:
    detector_id: str
    source_fingerprint: str
    state: str
    evidence_id: str
    def __post_init__(self):
        if self.state not in {"STABLE", "DRIFT", "UNKNOWN", "UNSUPPORTED"}:
            raise Refused("REFUSED[INVALID_DETECTOR_STATE]")
        if not self.evidence_id:
            raise Refused("REFUSED[EMPTY_DETECTOR_VOTE]")

def consensus(votes, independent_pairs=frozenset(), min_independent=2):
    if min_independent < 1:
        raise Refused("REFUSED[INVALID_INDEPENDENCE_FLOOR]")
    material = [vote for vote in votes if vote.state in {"STABLE", "DRIFT"}]
    if not material:
        return {"state": "INSUFFICIENT", "independent_count": 0}
    fingerprints = [vote.source_fingerprint for vote in material]
    if len(fingerprints) != len(set(fingerprints)):
        raise Refused("REFUSED[DUPLICATE_DETECTOR_SOURCE]")
    best = 0
    for size in range(1, len(material) + 1):
        for group in combinations(material, size):
            if all(frozenset((a.source_fingerprint, b.source_fingerprint)) in independent_pairs for a, b in combinations(group, 2)):
                best = max(best, size)
    states = {vote.state for vote in material}
    if best < min_independent:
        state = "INSUFFICIENT"
    elif len(states) > 1:
        state = "DIVERGED"
    elif states == {"DRIFT"}:
        state = "DRIFT_CONFIRMED"
    else:
        state = "STABLE_CONFIRMED"
    return {"state": state, "independent_count": best}
