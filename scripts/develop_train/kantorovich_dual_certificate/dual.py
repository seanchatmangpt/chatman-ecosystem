from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class DualPotential:
    source: tuple[tuple[str, Fraction], ...]
    target: tuple[tuple[str, Fraction], ...]
    def value(self, source_measure, target_measure):
        left = dict(self.source); right = dict(self.target)
        return sum((mass * left[key] for key, mass in source_measure.mass), Fraction(0)) + sum((mass * right[key] for key, mass in target_measure.mass), Fraction(0))
    def verify_feasible(self, metric):
        left = dict(self.source); right = dict(self.target)
        for a in left:
            for b in right:
                if left[a] + right[b] > metric.cost(a, b):
                    raise Refused("DUAL_INFEASIBLE", f"{a},{b}")
        return True

def derive_dual(plan, source, target, metric):
    nodes = [("S", key) for key in source.support] + [("T", key) for key in target.support]
    edges = []
    for left in source.support:
        for right in target.support:
            cost = metric.cost(left, right)
            edges.append((("T", right), ("S", left), cost))
            if plan.flow(left, right) > 0:
                edges.append((("S", left), ("T", right), -cost))
    values = {node: Fraction(0) for node in nodes}
    for index in range(len(nodes)):
        changed = False
        for src, dst, weight in edges:
            if values[dst] > values[src] + weight:
                values[dst] = values[src] + weight; changed = True
        if not changed:
            break
        if index == len(nodes) - 1:
            raise Refused("NO_DUAL_CERTIFICATE")
    dual = DualPotential(tuple((key, values[("S", key)]) for key in source.support), tuple((key, -values[("T", key)]) for key in target.support))
    dual.verify_feasible(metric)
    return dual
