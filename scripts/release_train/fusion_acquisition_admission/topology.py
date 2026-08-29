from enum import Enum
from .divergence import jensen_shannon

class FusionTopology(str, Enum):
    HEALTHY="HEALTHY"
    CORRELATED="CORRELATED"
    DIVERGENT="DIVERGENT"
    UNDER_SUPPORTED="UNDER_SUPPORTED"
    STALE="STALE"

def classify(calibrations, observations, independent_ids, fused, min_support=8, max_js=0.35):
    if any(c.support < min_support for c in calibrations):
        return FusionTopology.UNDER_SUPPORTED
    if len(independent_ids) < 2:
        return FusionTopology.CORRELATED
    if any(o.verdict == "STALE" for o in observations) and fused.verdict != "STALE":
        return FusionTopology.DIVERGENT
    distributions=[(float(c.false_current_rate), float(c.false_stale_rate), float(c.ambiguity_rate)) for c in calibrations]
    for i,left in enumerate(distributions):
        for right in distributions[i+1:]:
            if jensen_shannon(left, right) > max_js:
                return FusionTopology.DIVERGENT
    if fused.verdict == "AMBIGUOUS":
        return FusionTopology.DIVERGENT
    return FusionTopology.HEALTHY
