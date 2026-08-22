from dataclasses import dataclass
from .information import expected_information_gain
from .budget import fits_budget
from .dependence import independent
from .subject import Refused

STRATEGIES={"MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY"}

@dataclass(frozen=True)
class RankedCandidate:
    candidate: object
    information_gain: float
    score: float

def rank_candidates(belief,candidates,calibrations,strategy):
    if strategy not in STRATEGIES:
        raise Refused("REFUSED[UNKNOWN_ACQUISITION_STRATEGY]")
    cal={x.candidate_id:x for x in calibrations}
    rows=[]
    for c in candidates:
        g=expected_information_gain(belief,cal[c.candidate_id])
        if strategy=="MAX_INFORMATION_GAIN": score=g
        elif strategy=="MAX_INFORMATION_PER_COST": score=g/(float(c.cost) if c.cost else 1e-12)
        else: score=g
        rows.append(RankedCandidate(c,g,score))
    return tuple(sorted(rows,key=lambda r:(-r.score,-r.information_gain,r.candidate.cost,r.candidate.candidate_id)))

def select_measurements(belief,candidates,calibrations,budget,proofs=(),strategy="MAX_INFORMATION_GAIN"):
    ranked=rank_candidates(belief,candidates,calibrations,strategy)
    selected=[]
    for row in ranked:
        if row.information_gain <= 0: continue
        if not fits_budget(selected,row.candidate,budget): continue
        if not independent(row.candidate,selected,proofs): continue
        selected.append(row.candidate)
    return tuple(selected)
