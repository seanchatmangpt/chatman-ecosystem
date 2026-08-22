from dataclasses import dataclass
from enum import Enum
class Strategy(str,Enum):
    MAX_INFORMATION_GAIN='MAX_INFORMATION_GAIN'; MAX_INFORMATION_PER_COST='MAX_INFORMATION_PER_COST'; MIN_EXPECTED_ENTROPY='MIN_EXPECTED_ENTROPY'
@dataclass(frozen=True, slots=True)
class CandidateScore:
    candidate:object; information_gain:float; prior_entropy:float; expected_entropy:float
def rank(scores,strategy):
    def k(s):
        if strategy is Strategy.MAX_INFORMATION_GAIN: primary=s.information_gain
        elif strategy is Strategy.MAX_INFORMATION_PER_COST: primary=s.information_gain/(float(s.candidate.cost) if s.candidate.cost>0 else 1e-12)
        else: primary=-s.expected_entropy
        return (-primary,s.candidate.cost,s.candidate.latency_ms,s.candidate.candidate_id)
    return sorted(scores,key=k)
