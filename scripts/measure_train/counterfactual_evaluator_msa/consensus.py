from fractions import Fraction
from .robust import median, median_absolute_deviation
from .independence import require_independent
from .refusal import Refused

def estimator_consensus(estimates, identities, proofs, max_mad=Fraction(1,4)):
    if len(estimates)<2 or len(identities)<2: raise Refused("REFUSED[INSUFFICIENT_ESTIMATOR_DIVERSITY]")
    for i in range(len(identities)):
        for j in range(i+1,len(identities)):
            require_independent(identities[i],identities[j],proofs)
    center=median(estimates); mad=median_absolute_deviation(estimates)
    return {"state":"DIVERGED" if mad>max_mad else "COHERENT","center":center,"mad":mad}
