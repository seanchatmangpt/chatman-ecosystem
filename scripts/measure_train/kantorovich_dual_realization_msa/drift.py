from fractions import Fraction
def cusum(values,target=Fraction(0),threshold=Fraction(1,5)):
    s=Fraction(0)
    for v in values:
        s=max(Fraction(0),s+(v-target))
        if s>threshold:return "DRIFT"
    return "STABLE"
