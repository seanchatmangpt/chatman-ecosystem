from dataclasses import dataclass
@dataclass(frozen=True)
class Sensitivity:
    endpoint_displacement:float; width_displacement:float
def compare(a,b):
    return Sensitivity(abs(a.lo-b.lo)+abs(a.hi-b.hi), abs(a.width-b.width))
