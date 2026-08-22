from dataclasses import dataclass
from .subject import Refusal
from .information import binary_entropy,expected_information_gain
from .frontier import CalibrationFrontier
from .strategies import CandidateScore
from .independence import admitted_pairs
from .selector import select
from .standing import bounded_standing
from .receipt import issue
@dataclass(frozen=True, slots=True)
class Qualification:
    selection:object; standing:object; receipt:object
def qualify(*,subject,belief,candidates,calibrations,proofs,budget,strategy,now,expected_frontier=None,dependency_states=None):
    by_id={c.candidate_id:c for c in candidates}
    if len(by_id)!=len(candidates): raise Refusal('REFUSED_DUPLICATE_EVIDENCE_CANDIDATE')
    cal_by_id={}
    for c in calibrations:
        c.admit(now=now)
        if c.candidate_id in cal_by_id: raise Refusal('REFUSED_DUPLICATE_CALIBRATION')
        if c.candidate_id not in by_id: raise Refusal('REFUSED_FOREIGN_CALIBRATION')
        cal_by_id[c.candidate_id]=c
    frontier=CalibrationFrontier.build(calibrations)
    if expected_frontier is not None: expected_frontier.assert_current(frontier)
    h=binary_entropy(belief.defect); scores=[]
    for cid,c in by_id.items():
        cal=cal_by_id.get(cid)
        if cal is None: continue
        gain=expected_information_gain(belief,tpr=cal.true_positive_rate,fpr=cal.false_positive_rate)
        scores.append(CandidateScore(c,gain,h,h-gain))
    chosen=select(scores,strategy,budget,admitted_pairs(candidates,proofs))
    standing=bounded_standing(selected_count=len(chosen.candidate_ids),dependency_states=dependency_states or [])
    return Qualification(chosen,standing,issue(subject,frontier.digest,strategy,chosen.candidate_ids,standing.value))
