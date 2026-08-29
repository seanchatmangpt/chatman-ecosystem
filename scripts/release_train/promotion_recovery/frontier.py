import hashlib, json
from dataclasses import dataclass
from .subject import Refusal

@dataclass(frozen=True, order=True)
class CutCandidate:
    cut_id: str
    generation: int
    freshness: int
    skew: int
    complete: bool=True
    def __post_init__(self):
        if not self.cut_id or self.generation < 0 or self.freshness < 0 or self.skew < 0:
            raise Refusal('REFUSED[INVALID_CUT_CANDIDATE]')

class CandidateFrontier:
    def __init__(self, candidates):
        self.candidates=tuple(sorted(candidates))
        ids=[c.cut_id for c in self.candidates]
        if not self.candidates or len(ids)!=len(set(ids)):
            raise Refusal('REFUSED[INVALID_CANDIDATE_FRONTIER]')
    @property
    def digest(self):
        body=[c.__dict__ for c in self.candidates]
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def select(self, strategy):
        complete=[c for c in self.candidates if c.complete]
        if not complete: raise Refusal('REFUSED[NO_COMPLETE_CUT]')
        if strategy=='LATEST_COMPLETE': key=lambda c:(c.generation,c.freshness,-c.skew,c.cut_id)
        elif strategy=='MAX_FRESHNESS': key=lambda c:(c.freshness,c.generation,-c.skew,c.cut_id)
        elif strategy=='MIN_SKEW': key=lambda c:(-c.skew,c.freshness,c.generation,c.cut_id)
        else: raise Refusal('REFUSED[UNKNOWN_SELECTION_STRATEGY]')
        return max(complete,key=key)
