from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class GroundMetric:
    costs: tuple[tuple[str, str, Fraction], ...]
    @classmethod
    def from_mapping(cls, support, mapping):
        support = tuple(sorted(set(support)))
        costs = {}
        for left in support:
            for right in support:
                if (left, right) not in mapping:
                    raise Refused("MISSING_GROUND_COST", f"{left},{right}")
                cost = Fraction(mapping[(left, right)])
                if cost < 0:
                    raise Refused("NEGATIVE_GROUND_COST")
                costs[(left, right)] = cost
        for left in support:
            if costs[(left, left)] != 0:
                raise Refused("NONZERO_METRIC_DIAGONAL", left)
            for right in support:
                if costs[(left, right)] != costs[(right, left)]:
                    raise Refused("ASYMMETRIC_GROUND_METRIC")
                for pivot in support:
                    if costs[(left, pivot)] > costs[(left, right)] + costs[(right, pivot)]:
                        raise Refused("TRIANGLE_INEQUALITY_VIOLATION", f"{left},{right},{pivot}")
        return cls(tuple((a, b, c) for (a, b), c in sorted(costs.items())))
    def cost(self, left, right):
        for a, b, cost in self.costs:
            if a == left and b == right:
                return cost
        raise Refused("MISSING_GROUND_COST", f"{left},{right}")
