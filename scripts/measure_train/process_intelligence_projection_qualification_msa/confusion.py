from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Confusion:
    support:int; false_equivalent:int; false_diverged:int; accuracy:Fraction
def classify(observations):
    labeled=[o for o in observations if o.oracle_label!="UNKNOWN" and o.state in {"PASS","FAIL"}]; n=len(labeled)
    if not n: return Confusion(0,0,0,Fraction(0))
    fe=sum(1 for o in labeled if o.state=="PASS" and o.oracle_label=="DIVERGED")
    fd=sum(1 for o in labeled if o.state=="FAIL" and o.oracle_label=="EQUIVALENT")
    return Confusion(n,fe,fd,Fraction(n-fe-fd,n))
