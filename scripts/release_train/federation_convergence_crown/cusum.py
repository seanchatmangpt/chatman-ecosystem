from fractions import Fraction
from .refusal import refuse
def positive_cusum(values,target,threshold):
    target=Fraction(target); threshold=Fraction(threshold)
    if threshold<0: refuse("INVALID_CUSUM_THRESHOLD")
    score=Fraction(0)
    for v in values:
        score=max(Fraction(0),score+Fraction(v)-target)
        if score>=threshold: return True,score
    return False,score
