from dataclasses import dataclass
import math
@dataclass(frozen=True)
class SensorMetrics:
    support:int; false_current:int; false_stale:int; ambiguity:int; accuracy:float; wilson_lower:float
def wilson_lower(successes,n,z=1.959963984540054):
    if n==0:return 0.0
    p=successes/n; d=1+z*z/n
    return max(0.0,(p+z*z/(2*n)-z*math.sqrt(p*(1-p)/n+z*z/(4*n*n)))/d)
def measure_trials(trials):
    trials=tuple(trials); n=len(trials); correct=fc=fs=amb=0
    for t in trials:
        truth_current=t.truth=="HEALTHY"
        if t.predicted=="AMBIGUOUS": amb+=1
        elif t.predicted=="CURRENT" and not truth_current: fc+=1
        elif t.predicted=="NOT_CURRENT" and truth_current: fs+=1
        else: correct+=1
    return SensorMetrics(n,fc,fs,amb,0.0 if n==0 else correct/n,wilson_lower(correct,n))
