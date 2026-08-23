from dataclasses import dataclass
from fractions import Fraction
from .support import importance_weight
from .evidence import admit_log
@dataclass(frozen=True, slots=True)
class WeightDiagnostics: ess:Fraction; max_to_mean:Fraction
def diagnostics(rows):
    rows=admit_log(rows); w=tuple(importance_weight(r) for r in rows); s=sum(w,Fraction()); sq=sum((x*x for x in w),Fraction()); ess=Fraction() if sq==0 else s*s/sq; mean=s/len(w); ratio=Fraction() if mean==0 else max(w)/mean
    return WeightDiagnostics(ess,ratio)
