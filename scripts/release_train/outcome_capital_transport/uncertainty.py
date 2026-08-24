from math import log, sqrt
from .errors import Refused

def empirical_bernstein(values, delta=0.05):
    xs=[float(v) for v in values]
    if len(xs)<2: raise Refused("INSUFFICIENT_UNCERTAINTY_SUPPORT")
    if not 0<delta<1: raise Refused("INVALID_DELTA")
    mean=sum(xs)/len(xs); var=sum((x-mean)**2 for x in xs)/(len(xs)-1)
    radius=sqrt(2*var*log(3/delta)/len(xs))+3*log(3/delta)/len(xs)
    return mean, radius
