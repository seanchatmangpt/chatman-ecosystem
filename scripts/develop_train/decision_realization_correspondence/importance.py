from fractions import Fraction

def horvitz_thompson(values, propensities):
    if len(values)!=len(propensities) or not values:
        raise ValueError("shape")
    return sum((v/p for v,p in zip(values,propensities)), Fraction()) / len(values)

def self_normalized(values, propensities):
    weights=[Fraction(1,1)/p for p in propensities]
    return sum((w*v for w,v in zip(weights,values)), Fraction()) / sum(weights, Fraction())
