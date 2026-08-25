from math import log2
def binary_entropy(p:float)->float:
    if p<=0 or p>=1: return 0.0
    return -p*log2(p)-(1-p)*log2(1-p)
def information_gain(prior_error:float,posterior_error:float)->float:
    return binary_entropy(prior_error)-binary_entropy(posterior_error)
