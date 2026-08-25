from dataclasses import dataclass
from fractions import Fraction
from .calibration import require_current
from .diagnostics import diagnostics
from .estimators import Estimator,estimate
from .sensitivity import gamma_interval,breakdown_gamma
from .intervals import CandidateInterval,pareto
from .strategies import RobustStrategy,select
from .receipt import Receipt
from .authority import ActionClass,admit
@dataclass(frozen=True, slots=True)
class Evaluation: selected:CandidateInterval; frontier:tuple; standing:str; receipt:Receipt
class RobustPolicyEngine:
    def evaluate(self,subject,policy,rows,calibrations,gamma=Fraction(3,2),strategy=RobustStrategy.MAX_LOWER):
        admit(ActionClass.CONSTRUCT); require_current(calibrations); d=diagnostics(rows); candidates=[]
        for e in (Estimator.IPS,Estimator.SNIPS):
            point=estimate(rows,e).value; iv=gamma_interval(rows,gamma); lo=max(Fraction(0),min(iv.lower,point)); hi=max(lo,max(iv.upper,point))
            candidates.append(CandidateInterval(policy.digest+':'+e.value,type(iv)(lo,hi),breakdown_gamma(rows,point)))
        front=pareto(candidates); chosen=select(front,strategy); standing='PARTIAL_ALIVE' if d.ess >= 2 and d.max_to_mean <= 3 else 'UNKNOWN'
        receipt=Receipt(subject.value,policy.generation,chosen.policy_digest,strategy.value,standing,False)
        return Evaluation(chosen,front,standing,receipt)
