from dataclasses import dataclass
from .normalize import activity
@dataclass(frozen=True)
class Divergence:
    index:int; left:str|None; right:str|None
def minimal(a,b):
    x,y=activity(a),activity(b); n=max(len(x),len(y))
    for i in range(n):
        l=x[i] if i<len(x) else None; r=y[i] if i<len(y) else None
        if l!=r:return Divergence(i,l,r)
    return None
