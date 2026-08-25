from dataclasses import dataclass
from datetime import datetime, timezone
from .policy import Decision
from .errors import Refused

@dataclass(frozen=True)
class OutcomeObservation:
    observation_id: str
    policy_generation: int
    decision: Decision
    truth_independent: bool | None
    predicted_risk: float
    propensity: float
    realized_cost: float
    methodology: str
    engine: str
    region: str
    evidence_root: str
    observed_at: datetime

    def __post_init__(self):
        if not self.observation_id:
            raise Refused("EMPTY_OBSERVATION_ID")
        if self.policy_generation < 0:
            raise Refused("INVALID_GENERATION")
        if not (0 <= self.predicted_risk <= 1):
            raise Refused("INVALID_PREDICTED_RISK")
        if not (0 < self.propensity <= 1):
            raise Refused("INVALID_PROPENSITY")
        if self.realized_cost < 0:
            raise Refused("NEGATIVE_REALIZED_COST")
        if self.observed_at.tzinfo is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
        if any(not x for x in (self.methodology, self.engine, self.region, self.evidence_root)):
            raise Refused("INCOMPLETE_STRATUM_IDENTITY")

def admit(observations, policy_generation: int):
    obs = tuple(observations)
    if not obs:
        raise Refused("EMPTY_REALIZATION_SET")
    ids = [o.observation_id for o in obs]
    if len(ids) != len(set(ids)):
        raise Refused("DUPLICATE_OBSERVATION")
    now = datetime.now(timezone.utc)
    for o in obs:
        if o.policy_generation != policy_generation:
            raise Refused("FOREIGN_POLICY_GENERATION")
        if o.observed_at > now:
            raise Refused("FUTURE_OBSERVATION")
    return tuple(sorted(obs, key=lambda x: (x.observed_at, x.observation_id)))
