from dataclasses import dataclass
from .belief import BeliefState
from .probability import shannon_bits

@dataclass(frozen=True)
class InformationRealization:
    predicted_bits: float
    realized_bits: float

    @property
    def error_bits(self) -> float:
        return self.realized_bits - self.predicted_bits

def realized_information(prior: BeliefState, posterior: BeliefState, predicted_bits: float) -> InformationRealization:
    return InformationRealization(predicted_bits, shannon_bits(prior.probabilities) - shannon_bits(posterior.probabilities))
