from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class CusumResult:
    score:Fraction; threshold:Fraction; drifted:bool
def cusum_loss(losses,target,slack,threshold):
    score=Fraction(0)
    for loss in losses: score=max(Fraction(0),score+(loss-target-slack))
    return CusumResult(score,threshold,score>=threshold)
