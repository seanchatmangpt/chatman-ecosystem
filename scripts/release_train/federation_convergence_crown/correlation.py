from fractions import Fraction
from .refusal import refuse
def phi_squared(a,b,c,d):
    if min(a,b,c,d)<0: refuse("NEGATIVE_CONTINGENCY")
    den=(a+b)*(c+d)*(a+c)*(b+d)
    if den==0: refuse("DEGENERATE_CONTINGENCY")
    return Fraction((a*d-b*c)**2,den)
def independent_enough(value, threshold):
    threshold=Fraction(threshold)
    if not 0<=threshold<=1: refuse("INVALID_CORRELATION_THRESHOLD")
    return value<=threshold*threshold
