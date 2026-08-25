from dataclasses import dataclass
from fractions import Fraction
from .health import Health, PolicyHealth
from .policy import FeedbackStrategy

@dataclass(frozen=True)
class FeedbackCandidate:
    strategy: FeedbackStrategy
    calibration_error: Fraction
    regret: Fraction
    exploration_cost: Fraction

def candidates(health: PolicyHealth, *, bias: Fraction, regret: Fraction):
    base={
        FeedbackStrategy.HOLD: (abs(bias), regret, Fraction(0)),
        FeedbackStrategy.BIAS_CORRECT: (abs(bias)/2, regret, Fraction(1,10)),
        FeedbackStrategy.DOWNSHIFT_UNDERPERFORMER: (abs(bias), regret/2, Fraction(1,5)),
        FeedbackStrategy.EXPLORE_DRIFT: (abs(bias)*2/3, regret*2/3, Fraction(1,3)),
        FeedbackStrategy.MINIMAX_REGRET: (abs(bias), regret/3, Fraction(1,4)),
    }
    out=[FeedbackCandidate(k,*v) for k,v in base.items()]
    if health.state is Health.HEALTHY:
        out=[x for x in out if x.strategy in {FeedbackStrategy.HOLD, FeedbackStrategy.MINIMAX_REGRET}]
    return tuple(out)
