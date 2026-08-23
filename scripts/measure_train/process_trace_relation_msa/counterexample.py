from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class Counterexample:
    prefix_length:int
    left:tuple
    right:tuple

def minimal_counterexample(left,right):
    n=min(len(left),len(right))
    for i in range(n):
        if left[i]!=right[i]:
            return Counterexample(i+1,tuple(left[:i+1]),tuple(right[:i+1]))
    if len(left)!=len(right):
        return Counterexample(n+1,tuple(left[:n+1]),tuple(right[:n+1]))
    raise Refused("REFUSED[NO_DIVERGENCE]")
