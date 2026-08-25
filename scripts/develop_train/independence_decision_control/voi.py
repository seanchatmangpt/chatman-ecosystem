from dataclasses import dataclass
from fractions import Fraction


@dataclass(frozen=True)
class InformationOption:
    expected_risk_reduction: Fraction
    cost: Fraction
    latency_penalty: Fraction = Fraction(0)

    @property
    def net_value(self):
        return self.expected_risk_reduction - self.cost - self.latency_penalty

    @property
    def worth_acquiring(self):
        return self.net_value > 0
