from dataclasses import dataclass
from .moments import Moments
from .drift import DriftState
from .policy import Policy

@dataclass(frozen=True)
class StrategyEvidence:
    support: int
    failure_rate: float
    cost_ratio: float
    latency_ratio: float
    utility: Moments
    drift: DriftState

def admit_evidence(e: StrategyEvidence, p: Policy):
    if e.support < p.min_support:
        raise ValueError("REFUSED[UNDER_SUPPORTED_STRATEGY]")
    if e.failure_rate > p.max_failure_rate:
        raise ValueError("REFUSED[FAILURE_RATE_EXCEEDED]")
    if e.cost_ratio > p.max_cost_ratio:
        raise ValueError("REFUSED[COST_RATIO_EXCEEDED]")
    if e.latency_ratio > p.max_latency_ratio:
        raise ValueError("REFUSED[LATENCY_RATIO_EXCEEDED]")
    if e.drift.drifted:
        raise ValueError("REFUSED[POLICY_DRIFT]")
    return e
