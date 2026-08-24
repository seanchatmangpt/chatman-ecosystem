from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class TransportPlan:
    flows: tuple[tuple[str, str, Fraction], ...]
    def flow(self, left, right):
        return next((value for a, b, value in self.flows if a == left and b == right), Fraction(0))
    def cost(self, metric):
        return sum((value * metric.cost(a, b) for a, b, value in self.flows), Fraction(0))
    def verify_marginals(self, source, target):
        sm = source.as_dict(); tm = target.as_dict()
        for key, mass in sm.items():
            if sum((value for left, _, value in self.flows if left == key), Fraction(0)) != mass:
                raise Refused("SOURCE_MARGINAL_MISMATCH", key)
        for key, mass in tm.items():
            if sum((value for _, right, value in self.flows if right == key), Fraction(0)) != mass:
                raise Refused("TARGET_MARGINAL_MISMATCH", key)
        if any(value < 0 for _, _, value in self.flows):
            raise Refused("NEGATIVE_FLOW")
        return True
