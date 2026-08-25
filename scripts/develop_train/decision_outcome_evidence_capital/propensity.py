from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class SupportProfile:
    n: int
    min_propensity: float
    max_weight: float
    effective_sample_size: float

    @property
    def admitted(self):
        return self.n >= 5 and self.min_propensity >= 0.05 and self.effective_sample_size >= 3

def profile(observations) -> SupportProfile:
    obs = tuple(observations)
    if not obs:
        raise Refused("EMPTY_PROPENSITY_SAMPLE")
    weights = [1.0 / o.propensity for o in obs]
    s = sum(weights)
    ss = sum(w*w for w in weights)
    ess = (s*s/ss) if ss else 0.0
    return SupportProfile(len(obs), min(o.propensity for o in obs), max(weights), ess)

def require_support(p: SupportProfile):
    if not p.admitted:
        raise Refused("INSUFFICIENT_PROPENSITY_SUPPORT")
    return p
