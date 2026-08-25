from dataclasses import dataclass
from .relation import Relation
from .frontier import CalibrationFrontier
from .metamorphic import MetamorphicWitness
from .oracle import require_independent
from .wilson import wilson_upper
from .refusal import Refused

@dataclass(frozen=True)
class AdmissionThresholds:
    min_support: int = 30
    max_false_equivalence_upper: float = 0.20
    max_false_refusal_upper: float = 0.30

def admit_relation(relation: Relation, frontier: CalibrationFrontier, metamorphic: MetamorphicWitness, oracles, thresholds=AdmissionThresholds()):
    evidence = frontier.get(relation)
    if evidence.support < thresholds.min_support:
        raise Refused("REFUSED[INSUFFICIENT_CALIBRATION_SUPPORT]")
    metamorphic.require()
    require_independent(oracles)
    if wilson_upper(evidence.false_equivalence, evidence.support) > thresholds.max_false_equivalence_upper:
        raise Refused("REFUSED[FALSE_EQUIVALENCE_TOO_HIGH]")
    if wilson_upper(evidence.false_refusal, evidence.support) > thresholds.max_false_refusal_upper:
        raise Refused("REFUSED[FALSE_REFUSAL_TOO_HIGH]")
    return evidence
