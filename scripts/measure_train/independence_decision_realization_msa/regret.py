from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True, order=True)
class ObservedAlternative:
    decision_id:str; action:str; realized_loss:Fraction; observed:bool=True
def observed_regret(policy,rows,alternatives):
    by={}
    for alt in alternatives:
        if not alt.observed: raise Refused("REFUSED[UNOBSERVED_COUNTERFACTUAL]")
        by.setdefault(alt.decision_id,[]).append(alt)
    regrets=[]
    for row in rows:
        observed=by.get(row.decision_id,[])
        if not observed: continue
        actual=policy.realized_loss(row.decision,row.truth); best=min(a.realized_loss for a in observed)
        regrets.append(max(Fraction(0),actual-best))
    return {"support":len(regrets),"mean_regret":sum(regrets,Fraction(0))/len(regrets) if regrets else Fraction(0),"max_regret":max(regrets) if regrets else Fraction(0)}
