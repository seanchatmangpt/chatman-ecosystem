import math
from .predictive import pass_probability,posterior_defect
def binary_entropy(p):
    x=float(p)
    if x in (0.0,1.0): return 0.0
    return -x*math.log2(x)-(1-x)*math.log2(1-x)
def expected_information_gain(b,*,tpr,fpr):
    pp=pass_probability(b,tpr,fpr); a=posterior_defect(b,tpr=tpr,fpr=fpr,detects=False); d=posterior_defect(b,tpr=tpr,fpr=fpr,detects=True)
    return max(0.0,binary_entropy(b.defect)-(float(pp)*binary_entropy(a)+(1-float(pp))*binary_entropy(d)))
