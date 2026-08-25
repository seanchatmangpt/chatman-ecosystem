from dataclasses import dataclass
from fractions import Fraction
from .authority import ActionClass, admit_action
from .budget import FeedbackBudget
from .calibration import GainCalibration
from .drift import from_residuals
from .efficiency import Efficiency
from .health import classify
from .meta_policy import candidates
from .pareto import frontier
from .policy import FeedbackStrategy, PolicyIdentity
from .receipt import Receipt
from .standing import Standing
from .subject import Subject
from .trajectory import Trajectory
from .transition import PolicyTransition

@dataclass(frozen=True)
class Evaluation:
    health: object
    frontier: tuple
    selected: FeedbackStrategy
    transition: PolicyTransition | None
    standing: Standing
    receipt: Receipt

class FeedbackEngine:
    def evaluate(self, subject: Subject, policy: PolicyIdentity, trajectory: Trajectory, *, regret=Fraction(), budget=FeedbackBudget(2,Fraction(1))):
        calibration=GainCalibration.from_trajectory(trajectory)
        drift=from_residuals(trajectory.residuals)
        efficiency=Efficiency.from_trajectory(trajectory)
        health=classify(calibration,drift,efficiency)
        options=frontier(candidates(health,bias=calibration.bias,regret=regret))
        selected=min(options,key=lambda x:(x.calibration_error+x.regret+x.exploration_cost,x.strategy.value)).strategy
        transition=None
        if selected is not FeedbackStrategy.HOLD and budget.admits(0, next(x.exploration_cost for x in options if x.strategy is selected)):
            transition=PolicyTransition(policy,policy.generation+1,selected)
        standing=Standing.PARTIAL_ALIVE if health.state.value=="HEALTHY" and selected is FeedbackStrategy.HOLD else Standing.UNKNOWN
        admit_action(ActionClass.CONSTRUCT)
        receipt=Receipt(subject.value,policy.generation,selected.value,standing.value)
        return Evaluation(health,options,selected,transition,standing,receipt)
