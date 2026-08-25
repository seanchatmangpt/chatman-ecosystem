from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class KantorovichCertificate:
    primal_value: object
    dual_value: object
    gap: object
    complementary_slackness: bool
    weak_duality: bool

def verify_certificate(source, target, metric, plan, dual):
    plan.verify_marginals(source, target); dual.verify_feasible(metric)
    primal = plan.cost(metric); dual_value = dual.value(source, target)
    if dual_value > primal:
        raise Refused("WEAK_DUALITY_VIOLATION")
    left = dict(dual.source); right = dict(dual.target)
    slack = all(left[a] + right[b] == metric.cost(a, b) for a, b, value in plan.flows if value > 0)
    gap = primal - dual_value
    if gap != 0 or not slack:
        raise Refused("STRONG_DUALITY_NOT_CERTIFIED", f"gap={gap}")
    return KantorovichCertificate(primal, dual_value, gap, slack, True)
