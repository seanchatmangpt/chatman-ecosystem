from dataclasses import dataclass
from .strategies import rank
from .independence import pairwise_independent
@dataclass(frozen=True, slots=True)
class Selection:
    strategy:object; candidate_ids:tuple; total_information_gain:float
def select(scores,strategy,budget,independent_pairs):
    chosen=[]; info=0.0
    for s in rank(scores,strategy):
        trial=chosen+[s.candidate]; ids=[x.candidate_id for x in trial]
        if not budget.admits(trial): continue
        if len(ids)>1 and not pairwise_independent(ids,independent_pairs): continue
        if s.information_gain<=0: continue
        chosen=trial; info+=s.information_gain
    return Selection(strategy,tuple(c.candidate_id for c in chosen),info)
