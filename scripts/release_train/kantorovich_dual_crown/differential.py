from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class OracleWitness:
    implementation:str; model:str; value:Fraction
def require_independent(a,b,max_gap=Fraction(0)):
    if a.implementation==b.implementation or a.model==b.model: raise Refused("ORACLE_NOT_INDEPENDENT")
    gap=abs(Fraction(a.value)-Fraction(b.value))
    if gap>Fraction(max_gap): raise Refused("ORACLE_DISAGREEMENT",str(gap))
    return gap
