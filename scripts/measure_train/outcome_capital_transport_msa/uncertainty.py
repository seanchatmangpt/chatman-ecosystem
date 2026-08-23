import math
from dataclasses import dataclass
@dataclass(frozen=True)
class EmpiricalBernstein:
    mean: float
    variance: float
    radius: float
    lower: float
    upper: float
def bound(values,delta=0.05):
    xs=[float(x) for x in values]
    if len(xs)<2: return EmpiricalBernstein(xs[0] if xs else 0.0,0.0,1.0,0.0,1.0)
    n=len(xs); mean=sum(xs)/n
    var=sum((x-mean)**2 for x in xs)/(n-1)
    log=math.log(3.0/delta)
    radius=math.sqrt(2*var*log/n)+3*log/n
    return EmpiricalBernstein(mean,var,radius,max(0.0,mean-radius),min(1.0,mean+radius))
