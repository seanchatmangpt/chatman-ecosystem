from .refusal import Refused

def median(values):
    vals=sorted(values)
    if not vals: raise Refused("REFUSED[EMPTY_ROBUST_SAMPLE]")
    n=len(vals); m=n//2
    return vals[m] if n%2 else (vals[m-1]+vals[m])/2

def median_absolute_deviation(values):
    center=median(values)
    return median([abs(v-center) for v in values])
