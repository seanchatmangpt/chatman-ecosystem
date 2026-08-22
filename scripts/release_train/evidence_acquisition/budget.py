from dataclasses import dataclass

from .candidate import EvidenceCandidate

@dataclass(frozen=True)
class AcquisitionBudget:
    max_cost_milli: int
    max_latency_ms: int
    max_count: int

    def admit(self, candidates: tuple[EvidenceCandidate, ...]) -> None:
        if self.max_cost_milli < 0 or self.max_latency_ms < 0 or self.max_count < 1:
            raise ValueError("REFUSED[INVALID_ACQUISITION_BUDGET]")
        if len(candidates) > self.max_count:
            raise ValueError("REFUSED[ACQUISITION_COUNT_BUDGET]")
        if sum(candidate.cost_milli for candidate in candidates) > self.max_cost_milli:
            raise ValueError("REFUSED[ACQUISITION_COST_BUDGET]")
        if sum(candidate.latency_ms for candidate in candidates) > self.max_latency_ms:
            raise ValueError("REFUSED[ACQUISITION_LATENCY_BUDGET]")
