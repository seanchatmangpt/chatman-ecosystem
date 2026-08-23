from dataclasses import dataclass
from fractions import Fraction
from .authority import ActionClass,admit_action
from .calibration import GainCalibration
from .drift import detect
from .efficiency import Efficiency
from .frontier import PolicyFrontier
from .regret import realized_regret
from .standing import derive
from .strategies import candidates,select
from .receipt import manufacture
@dataclass(frozen=True)
class Qualification:
    standing: str
    reason: str
    selected_strategy: str|None
    blockers: tuple
    phases: tuple
    receipt: object
def qualify(*,subject,policy,frontier,trajectory,dependencies=None,alternatives=(),now=None):
    PolicyFrontier(tuple(frontier)).require(policy)
    if now is not None and trajectory.steps[-1].observed_at > now: raise ValueError("REFUSED[FUTURE_EVIDENCE]")
    blockers=dependencies.blockers(subject.repo) if dependencies else ()
    failed=any(s.outcome=="FAIL" for s in trajectory.steps)
    cal=GainCalibration.from_residuals(trajectory.residuals)
    reliable=True
    try: cal.admit()
    except Exception: reliable=False
    drift=detect(trajectory.residuals).drifted
    eff=None; regret=Fraction(0); selected=None
    if not failed and not blockers and reliable and not drift:
        eff=Efficiency.from_trajectory(trajectory)
        regret=realized_regret(trajectory.steps[-1].realized_gain, alternatives) if alternatives else Fraction(0)
        selected=select(candidates(cal,drift,eff,regret)).strategy.value
    hold=selected=="HOLD"
    standing=derive(blockers=blockers,failed=failed,drifted=drift,reliable=reliable,hold=hold)
    reason=("DEPENDENCY_BLOCKED" if blockers else "FAILED_EVIDENCE" if failed else
            "DRIFTED_POLICY" if drift else "UNRELIABLE_POLICY" if not reliable else
            "CURRENT_POLICY_HOLD" if hold else "REQUALIFY_POLICY")
    admit_action(ActionClass.SELECT); admit_action(ActionClass.CONSTRUCT); admit_action(ActionClass.VERIFY)
    body={"schema":"chatman.realized-feedback-admission/1","subject":subject.exact,
          "policy_generation":policy.generation,"policy_digest":policy.digest,
          "selected_strategy":selected,"standing":standing,"reason":reason,
          "blockers":list(blockers),"authority":"SELECT",
          "phases":["VERIFY","CONSTRUCT"],"actuation_performed":False}
    return Qualification(standing,reason,selected,blockers,("VERIFY","CONSTRUCT"),manufacture(body))
