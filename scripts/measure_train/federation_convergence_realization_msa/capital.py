from dataclasses import dataclass
from fractions import Fraction
from .refusals import Refused
@dataclass(frozen=True)
class Source:
    source_id:str; implementation_digest:str; model_digest:str; cause:str
def effective(sources,rho=Fraction(0)):
    rows=tuple(sources)
    if not rows: return Fraction(0)
    if rho<0 or rho>1: raise Refused('REFUSED[INVALID_CORRELATION]')
    n=Fraction(len(rows)); ess=n/(1+(n-1)*rho)
    return min(ess,Fraction(len({s.implementation_digest for s in rows})),Fraction(len({s.model_digest for s in rows})),Fraction(len({s.cause for s in rows})))
