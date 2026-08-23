from dataclasses import replace
from fractions import Fraction
from hashlib import sha256
from .utility import PolicyBound
class FailureWorld:
    def __init__(self, seed:str): self.seed=seed
    def apply(self,bounds:tuple[PolicyBound,...])->tuple[PolicyBound,...]:
        out=[]
        for b in sorted(bounds,key=lambda x:x.policy.digest):
            h=int(sha256((self.seed+b.policy.digest).encode()).hexdigest(),16)
            if h%7==0: continue
            shock=Fraction(h%5,100)
            out.append(replace(b, utility=type(b.utility)(b.utility.lower-shock,b.utility.upper+shock)))
        return tuple(out)
