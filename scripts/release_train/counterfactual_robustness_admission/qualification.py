from dataclasses import dataclass
from fractions import Fraction
from .authority import ActionClass,admit_action
from .calibration import require_quality
from .candidates import select
from .frontier import CalibrationFrontier
from .independence import require_independent
from .standing import derive
from .support import profile,require_support
from .receipt import manufacture

@dataclass(frozen=True)
class Qualification:
    standing: str
    reason: str
    selected_policy_digest: str|None
    blockers: tuple
    phases: tuple
    receipt: object

def qualify(*,subject,current_policy,calibrations,proof_pairs,logs,candidates,strategy,dependencies=None,failed=False,min_lower=Fraction(1,5)):
    blockers=dependencies.blockers(subject.repo) if dependencies else ()
    supported=True
    try:
        require_support(profile(logs))
        frontier=CalibrationFrontier(tuple(calibrations))
        current=tuple(require_quality(c) for c in frontier.current())
        if len(current)<2: raise ValueError('insufficient')
        require_independent(current[0],current[1],proof_pairs)
    except Exception:
        supported=False
    selected=None; robust=False
    if supported and not blockers and not failed:
        selected=select(tuple(candidates),strategy,current_policy.digest)
        robust=selected.interval.lower>=min_lower
    standing=derive(blockers=blockers,failed=failed,robust=robust,supported=supported)
    reason=('DEPENDENCY_BLOCKED' if blockers else 'FAILED_EVIDENCE' if failed else 'INSUFFICIENT_ROBUST_EVIDENCE' if not supported else 'ROBUST_CURRENT_POLICY' if robust else 'ROBUSTNESS_REQUALIFICATION_REQUIRED')
    for a in (ActionClass.SELECT,ActionClass.CONSTRUCT,ActionClass.VERIFY): admit_action(a)
    body={'schema':'chatman.counterfactual-robustness-admission/1','subject':subject.exact,'policy_generation':current_policy.generation,'policy_digest':current_policy.digest,'strategy':strategy.value,'selected_policy_digest':selected.policy_digest if selected else None,'standing':standing,'reason':reason,'blockers':list(blockers),'authority':'SELECT','phases':['VERIFY','CONSTRUCT'],'actuation_performed':False}
    return Qualification(standing,reason,selected.policy_digest if selected else None,blockers,('VERIFY','CONSTRUCT'),manufacture(body))
