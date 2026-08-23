from dataclasses import dataclass
from fractions import Fraction
from .rational import nonnegative
@dataclass(frozen=True)
class DebtLedger:
    information:Fraction=Fraction(0); cost_slip:Fraction=Fraction(0); latency_slip:Fraction=Fraction(0)
    def __post_init__(self):
        for n in ("information","cost_slip","latency_slip"): object.__setattr__(self,n,nonnegative(getattr(self,n)))
    def advance(self,realization,*,planned_cost,planned_latency):
        pc,pl=nonnegative(planned_cost),nonnegative(planned_latency)
        return DebtLedger(self.information+realization.information_debt,self.cost_slip+max(Fraction(0),realization.cost-pc),self.latency_slip+max(Fraction(0),realization.latency-pl))
    def within(self,*,max_information,max_cost_slip,max_latency_slip):
        return self.information<=max_information and self.cost_slip<=max_cost_slip and self.latency_slip<=max_latency_slip
