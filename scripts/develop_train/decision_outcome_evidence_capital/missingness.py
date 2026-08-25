from dataclasses import dataclass
from enum import Enum
from .errors import Refused

class Missingness(str, Enum):
    OBSERVED = "OBSERVED"
    DEFERRED = "DEFERRED"
    UNLABELED = "UNLABELED"

@dataclass(frozen=True)
class MissingnessProfile:
    observed: int
    deferred: int
    unlabeled: int

    @property
    def observed_fraction(self):
        total = self.observed + self.deferred + self.unlabeled
        return self.observed / total if total else 0.0

def classify(observations):
    obs = tuple(observations)
    observed = sum(o.truth_independent is not None for o in obs)
    deferred = sum(o.decision.value == "DEFER" for o in obs)
    unlabeled = len(obs) - observed
    return MissingnessProfile(observed, deferred, unlabeled)

def require_observed(profile: MissingnessProfile, minimum_fraction=0.5):
    if profile.observed_fraction < minimum_fraction:
        raise Refused("INSUFFICIENT_OUTCOME_OBSERVATION")
    return profile
