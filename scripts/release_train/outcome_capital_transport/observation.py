from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .rational import unit, nonnegative

@dataclass(frozen=True)
class OutcomeObservation:
    observation_id: str
    generation: int
    decision: str
    truth: str
    propensity: Fraction
    realized_cost: Fraction
    methodology: str
    engine: str
    region: str
    evidence_root: str

    def __post_init__(self):
        if not self.observation_id or self.generation < 0:
            raise Refused("INVALID_OBSERVATION_IDENTITY")
        if self.decision not in {"INDEPENDENT", "DEPENDENT", "DEFER"}:
            raise Refused("INVALID_DECISION", self.decision)
        if self.truth not in {"INDEPENDENT", "DEPENDENT"}:
            raise Refused("INVALID_TRUTH", self.truth)
        object.__setattr__(self, "propensity", unit(self.propensity, "propensity"))
        if self.propensity == 0:
            raise Refused("POSITIVITY_VIOLATION")
        object.__setattr__(self, "realized_cost", nonnegative(self.realized_cost, "realized_cost"))
        for name in ("methodology", "engine", "region", "evidence_root"):
            if not getattr(self, name):
                raise Refused("MISSING_STRATUM_IDENTITY", name)

def admit(observations, generation):
    seen = set()
    out = []
    for obs in observations:
        if obs.observation_id in seen:
            raise Refused("DUPLICATE_OBSERVATION", obs.observation_id)
        if obs.generation != generation:
            raise Refused("FOREIGN_GENERATION", obs.observation_id)
        seen.add(obs.observation_id)
        out.append(obs)
    if not out:
        raise Refused("EMPTY_OBSERVATIONS")
    return tuple(out)
