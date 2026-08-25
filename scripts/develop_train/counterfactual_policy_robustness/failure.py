from dataclasses import replace
from fractions import Fraction
import hashlib
class FailureWorld:
    def __init__(self,seed): self.seed=seed
    def apply(self,rows):
        out=[]
        for r in sorted(rows,key=lambda x:x.case_id):
            h=int(hashlib.sha256((self.seed+r.case_id).encode()).hexdigest()[:8],16)
            if h % 11 == 0: continue
            reward=max(Fraction(0),min(Fraction(1),r.reward+(Fraction(1,20) if h%2 else Fraction(-1,20))))
            out.append(replace(r,reward=reward))
        return tuple(out)
