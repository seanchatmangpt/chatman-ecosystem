from fractions import Fraction
import math

def total_variation(source, target):
    s,t=source.as_dict(),target.as_dict(); keys=set(s)|set(t)
    return sum((abs(s.get(k,0)-t.get(k,0)) for k in keys), Fraction(0))/2

def jensen_shannon(source, target):
    s,t=source.as_dict(),target.as_dict(); keys=set(s)|set(t)
    def kl(p,m):
        return sum(float(p.get(k,0))*math.log2(float(p.get(k,0)/m[k])) for k in keys if p.get(k,0)>0)
    m={k:(s.get(k,0)+t.get(k,0))/2 for k in keys}
    return (kl(s,m)+kl(t,m))/2
