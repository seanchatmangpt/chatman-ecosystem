from dataclasses import dataclass
from fractions import Fraction
from .identity import PolicyIdentity
from .intervals import Interval
from .independence import EvidenceIdentity

@dataclass(frozen=True)
class PolicyBound:
    policy: PolicyIdentity
    interval: Interval
    breakdown_gamma: Fraction
    cost: Fraction
    latency: Fraction
    evidence: EvidenceIdentity
    calibration_generation: int
    calibration_digest: str
