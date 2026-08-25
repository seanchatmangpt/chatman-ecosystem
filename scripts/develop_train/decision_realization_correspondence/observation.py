from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

DECISIONS={"INDEPENDENT","DEPENDENT","DEFER"}
TRUTH={"INDEPENDENT","DEPENDENT"}

@dataclass(frozen=True)
class Observation:
    observation_id: str
    policy_generation: int
    decision: str
    truth: str | None
    predicted_risk: Fraction
    propensity: Fraction
    realized_cost: Fraction
    methodology: str
    engine: str
    region: str
    evidence_root: str
    def __post_init__(self):
        if not self.observation_id:
            raise Refused("EMPTY_OBSERVATION_ID")
        if self.decision not in DECISIONS or (self.truth is not None and self.truth not in TRUTH):
            raise Refused("INVALID_DECISION_OR_TRUTH")
        if not (0 <= self.predicted_risk <= 1):
            raise Refused("INVALID_PREDICTED_RISK")
        if not (0 < self.propensity <= 1):
            raise Refused("INVALID_PROPENSITY")
        if self.realized_cost < 0:
            raise Refused("NEGATIVE_REALIZED_COST")
