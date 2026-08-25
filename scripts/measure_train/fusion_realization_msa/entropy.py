import math
from .probability import normalize
def shannon_bits(values):
    p=normalize(values)
    return -sum(x*math.log2(x) for x in p if x>0)
