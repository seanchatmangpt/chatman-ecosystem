from fractions import Fraction
from collections import Counter

def effective_source_count(observations):
    counts=Counter(o.source.producer for o in observations)
    total=sum(counts.values())
    if total==0:
        return Fraction(0,1)
    return Fraction(total*total, sum(v*v for v in counts.values()))

def diversity_vector(observations):
    return {
        "producers": len({o.source.producer for o in observations}),
        "source_kinds": len({o.source.kind for o in observations}),
        "effective_sources": effective_source_count(observations),
    }
