from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class LabeledVerdict:
    expected:str
    observed:str

@dataclass(frozen=True)
class Calibration:
    support:int
    false_independent_rate:Fraction
    false_dependent_rate:Fraction
    state:str

def calibrate(rows, min_support=6, max_error=Fraction(1,5)):
    rows=tuple(rows)
    if not rows:
        return Calibration(0,Fraction(0),Fraction(0),"INSUFFICIENT")
    independent=[r for r in rows if r.expected=="INDEPENDENT"]
    dependent=[r for r in rows if r.expected=="DEPENDENT"]
    fi=sum(1 for r in dependent if r.observed=="INDEPENDENT")
    fd=sum(1 for r in independent if r.observed=="DEPENDENT")
    fir=Fraction(fi,len(dependent)) if dependent else Fraction(0)
    fdr=Fraction(fd,len(independent)) if independent else Fraction(0)
    state="INSUFFICIENT" if len(rows)<min_support or not independent or not dependent else ("CALIBRATED" if max(fir,fdr)<=max_error else "UNRELIABLE")
    return Calibration(len(rows),fir,fdr,state)
