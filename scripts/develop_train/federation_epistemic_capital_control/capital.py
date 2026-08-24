from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class EpistemicCapital: nominal:int; generalized_ess:Fraction; cause_units:int; provenance_units:int; effective:Fraction
def capital(evidence,ess,causes):
    xs=tuple(evidence); prov=len({(x.implementation,x.model,x.domain,x.evidence_root) for x in xs}); effective=min(ess.generalized,Fraction(causes.count),Fraction(prov))
    return EpistemicCapital(len(xs),ess.generalized,causes.count,prov,effective)
