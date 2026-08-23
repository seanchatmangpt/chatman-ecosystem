import math
from fractions import Fraction
from .fractions import unit

def binary_entropy(p: Fraction) -> float:
    p=unit(p,"probability")
    if p in (0,1): return 0.0
    x=float(p)
    return -x*math.log2(x)-(1-x)*math.log2(1-x)

def expected_information_gain(prior: Fraction, pass_probability: Fraction, posterior_if_pass: Fraction, posterior_if_fail: Fraction) -> float:
    prior=unit(prior,"prior"); pp=unit(pass_probability,"pass_probability")
    a=unit(posterior_if_pass,"posterior_if_pass"); b=unit(posterior_if_fail,"posterior_if_fail")
    return max(0.0, binary_entropy(prior)-float(pp)*binary_entropy(a)-float(1-pp)*binary_entropy(b))
