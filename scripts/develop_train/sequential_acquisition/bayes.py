from fractions import Fraction
from .belief import BeliefState
from .evidence import ObservationEvidence
from .refusals import Refused

def update(prior: BeliefState, evidence: ObservationEvidence) -> BeliefState:
    if set(prior.probabilities) != set(evidence.likelihoods):
        raise Refused("REFUSED_EVIDENCE_DIMENSION_MISMATCH")
    weights = {k: prior.probabilities[k] * evidence.likelihoods[k] for k in prior.probabilities}
    z = sum(weights.values(), Fraction())
    if z == 0:
        raise Refused("REFUSED_ZERO_EVIDENCE_MASS")
    posterior = {k: v / z for k, v in weights.items()}
    return BeliefState(prior.generation + 1, posterior)
