from dataclasses import dataclass

@dataclass(frozen=True)
class EvidenceBudget:
    max_detectors:int=8
    max_observations:int=512
    max_pair_proofs:int=64
    def admit(self, *, detectors, observations, proofs):
        if detectors>self.max_detectors or observations>self.max_observations or proofs>self.max_pair_proofs:
            raise ValueError("REFUSED[EVIDENCE_BUDGET_EXCEEDED]")
        return True
