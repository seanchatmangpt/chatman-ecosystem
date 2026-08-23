from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .evidence import admit_log
@dataclass(frozen=True, slots=True)
class SupportProfile:
    n:int; target_mass:Fraction; max_weight:Fraction; mean_weight:Fraction
def importance_weight(row):
    if row.target_p > 0 and row.behavior_p <= 0: raise Refused('REFUSED_POSITIVITY')
    return row.target_p/row.behavior_p
def profile(rows):
    rows=admit_log(rows); weights=tuple(importance_weight(r) for r in rows); mass=sum((r.target_p for r in rows),Fraction())
    if mass <= 0: raise Refused('REFUSED_ZERO_TARGET_MASS')
    return SupportProfile(len(rows),mass,max(weights),sum(weights,Fraction())/len(weights))
