from dataclasses import dataclass
@dataclass(frozen=True)
class Cusum:
    positive:float; negative:float; drifted:bool
def cusum(values,target,slack,threshold):
    pos=neg=0.0
    for x in values:
        d=float(x)-float(target); pos=max(0.0,pos+d-slack); neg=max(0.0,neg-d-slack)
    return Cusum(pos,neg,max(pos,neg)>=threshold)
