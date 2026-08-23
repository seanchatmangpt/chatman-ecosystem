from dataclasses import dataclass
from fractions import Fraction
from .policy import FeedbackStrategy
@dataclass(frozen=True)
class Candidate:
    strategy: FeedbackStrategy
    score: Fraction
    reversibility: Fraction
def candidates(calibration, drifted, efficiency, regret):
    out=[
      Candidate(FeedbackStrategy.HOLD, Fraction(1)-min(Fraction(1),calibration.mae), Fraction(1)),
      Candidate(FeedbackStrategy.BIAS_CORRECT, min(Fraction(1),abs(calibration.bias)+Fraction(1,10)), Fraction(4,5)),
      Candidate(FeedbackStrategy.DOWNSHIFT_UNDERPERFORMER, min(Fraction(1),Fraction(1,1)/max(Fraction(1,100),efficiency.bits_per_cost)), Fraction(3,4)),
      Candidate(FeedbackStrategy.EXPLORE_DRIFT, Fraction(1) if drifted else Fraction(1,10), Fraction(9,10)),
      Candidate(FeedbackStrategy.MINIMAX_REGRET, min(Fraction(1),Fraction(regret)+Fraction(1,10)), Fraction(4,5)),
    ]
    return tuple(out)
def select(items):
    return max(items,key=lambda c:(c.score,c.reversibility,c.strategy.value))
