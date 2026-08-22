from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused

SCOPES={"FOCUSED","REPOSITORY","RUNTIME","ARTIFACT","DEPENDENCY","RECEIPT"}
AUTHORITIES={"OBSERVE","SELECT","CONSTRUCT","DO"}

@dataclass(frozen=True, order=True)
class MeasurementCandidate:
    candidate_id: str
    sensor_family: str
    implementation_domain: str
    scope: str
    cost: Fraction
    latency_ms: int
    authority: str = "OBSERVE"
    def __post_init__(self):
        if not self.candidate_id.strip() or not self.sensor_family.strip() or not self.implementation_domain.strip():
            raise Refused("REFUSED[INVALID_MEASUREMENT_CANDIDATE]")
        if self.scope not in SCOPES:
            raise Refused("REFUSED[INVALID_MEASUREMENT_SCOPE]")
        if not isinstance(self.cost, Fraction) or self.cost < 0:
            raise Refused("REFUSED[INVALID_MEASUREMENT_COST]")
        if self.latency_ms < 0:
            raise Refused("REFUSED[INVALID_MEASUREMENT_LATENCY]")
        if self.authority not in AUTHORITIES:
            raise Refused("REFUSED[INVALID_AUTHORITY]")
        if self.authority == "DO":
            raise Refused("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
