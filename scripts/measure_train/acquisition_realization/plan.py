from dataclasses import dataclass
from fractions import Fraction
from .subject import Subject, Refused

STRATEGIES={"MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY"}

@dataclass(frozen=True, order=True)
class AcquisitionPlan:
    subject: Subject
    plan_id: str
    policy_generation: int
    strategy: str
    candidate_id: str
    predicted_gain: Fraction
    predicted_pass: Fraction
    cost: Fraction
    latency_ms: int
    frontier_digest: str

    def __post_init__(self):
        if not self.plan_id or not self.candidate_id:
            raise Refused("REFUSED[EMPTY_PLAN_IDENTITY]")
        if self.policy_generation < 0:
            raise Refused("REFUSED[INVALID_POLICY_GENERATION]")
        if self.strategy not in STRATEGIES:
            raise Refused("REFUSED[UNKNOWN_ACQUISITION_STRATEGY]")
        if not (Fraction(0) <= self.predicted_gain <= Fraction(1)):
            raise Refused("REFUSED[INVALID_PREDICTED_GAIN]")
        if not (Fraction(0) <= self.predicted_pass <= Fraction(1)):
            raise Refused("REFUSED[INVALID_PREDICTIVE_MASS]")
        if self.cost <= 0 or self.latency_ms < 0:
            raise Refused("REFUSED[INVALID_RESOURCE_PREDICTION]")
        if len(self.frontier_digest)!=64 or any(c not in '0123456789abcdef' for c in self.frontier_digest):
            raise Refused("REFUSED[INVALID_FRONTIER_DIGEST]")
