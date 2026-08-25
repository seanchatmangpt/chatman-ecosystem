from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class KantorovichCertificate:
    primal_cost:Fraction; dual_value:Fraction; max_slack:Fraction; tight_edges:int
def verify_certificate(source,target,metric,plan,dual):
    plan.verify_marginals(source,target); dual.require_feasible(metric)
    pc=plan.cost(metric); dv=dual.objective(source,target)
    if pc!=dv: raise Refused("STRONG_DUALITY_GAP",f"{pc}!={dv}")
    u=dict(dual.source); v=dict(dual.target); mx=Fraction(); tight=0
    for a,b,x in plan.flow:
        slack=metric.cost(a,b)-u[a]-v[b]
        if slack<0: raise Refused("NEGATIVE_DUAL_SLACK")
        mx=max(mx,slack)
        if x>0:
            if slack!=0: raise Refused("COMPLEMENTARY_SLACKNESS_VIOLATION",f"{a}->{b}")
            tight+=1
    return KantorovichCertificate(pc,dv,mx,tight)
