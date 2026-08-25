from fractions import Fraction
def cusum(values,target=Fraction(0),threshold=Fraction(1)):
    pos=neg=Fraction(0)
    for v in values:
        x=Fraction(v)-target; pos=max(Fraction(0),pos+x); neg=min(Fraction(0),neg+x)
        if pos>=threshold or -neg>=threshold: return True
    return False
