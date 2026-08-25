from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
import re
from .errors import Refused

_HEX = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class Observation:
    observation_id: str
    certificate_digest: str
    certificate_generation: int
    oracle_cost: Fraction
    realized_consequence: Fraction
    predicted_consequence_bound: Fraction
    validator_implementation: str
    validator_model: str
    evidence_root: str
    methodology: str
    engine: str
    region: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.observation_id:
            raise Refused("EMPTY_OBSERVATION_ID")
        if not _HEX.fullmatch(self.certificate_digest):
            raise Refused("INVALID_OBSERVATION_CERTIFICATE")
        if self.certificate_generation < 0:
            raise Refused("INVALID_OBSERVATION_GENERATION")
        if min(self.oracle_cost, self.realized_consequence, self.predicted_consequence_bound) < 0:
            raise Refused("NEGATIVE_OBSERVATION_VALUE")
        if self.observed_at.tzinfo is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
        if any(not x for x in (self.validator_implementation,self.validator_model,self.evidence_root,self.methodology,self.engine,self.region)):
            raise Refused("INCOMPLETE_OBSERVATION_PROVENANCE")
