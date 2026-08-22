from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class EvidenceCandidate:
    id: str
    family: str
    domain: str
    scope: str
    cost_milli: int
    latency_ms: int
    authority: str = "SELECT"
    def __post_init__(self):
        if not self.id or not self.family or not self.domain or not self.scope:
            raise ValueError("REFUSED[INVALID_CANDIDATE]")
        if self.cost_milli < 0 or self.latency_ms < 0:
            raise ValueError("REFUSED[INVALID_CANDIDATE_COST]")
        if self.authority != "SELECT":
            raise ValueError("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
