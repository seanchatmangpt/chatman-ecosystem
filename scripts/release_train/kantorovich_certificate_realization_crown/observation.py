from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class Observation:
    observation_id: str
    certificate_digest: str
    generation: int
    oracle_cost: Fraction
    realized_consequence: Fraction
    predicted_bound: Fraction
    implementation: str
    model: str
    root: str
    methodology: str
    engine: str
    region: str
    world: str
    def validate(self):
        if not self.observation_id or min(self.oracle_cost, self.realized_consequence, self.predicted_bound) < 0:
            raise Refused("INVALID_OBSERVATION")
        return self
