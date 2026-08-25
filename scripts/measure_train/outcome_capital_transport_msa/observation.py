from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject, Refused
METHODS={"DISCOVERY","CONFORMANCE","SIMULATION","PREDICTION","OPTIMIZATION","INTERVENTION","MONITORING","EVENT_CENTRIC","OBJECT_CENTRIC","DECLARATIVE","PROCEDURAL"}
@dataclass(frozen=True, order=True)
class OutcomeObservation:
    subject: Subject
    evidence_id: str
    methodology: str
    engine: str
    region: str
    evidence_root: str
    generation: int
    propensity: Fraction
    predicted_risk: Fraction
    decision: str
    truth: str
    observed_at: datetime
    def __post_init__(self):
        if not self.evidence_id or not self.engine or not self.region or not self.evidence_root:
            raise Refused("REFUSED[INVALID_OUTCOME_IDENTITY]")
        if self.methodology not in METHODS: raise Refused("REFUSED[UNKNOWN_METHODOLOGY]")
        if self.generation < 0: raise Refused("REFUSED[INVALID_GENERATION]")
        if self.propensity <= 0 or self.propensity > 1: raise Refused("REFUSED[POSITIVITY_VIOLATION]")
        if self.predicted_risk < 0 or self.predicted_risk > 1: raise Refused("REFUSED[INVALID_PREDICTED_RISK]")
        if self.decision not in {"INDEPENDENT","DEPENDENT","DEFER"}: raise Refused("REFUSED[INVALID_DECISION]")
        if self.truth not in {"INDEPENDENT","DEPENDENT","UNKNOWN"}: raise Refused("REFUSED[INVALID_TRUTH]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EVIDENCE_TIME]")
    @property
    def labeled(self): return self.truth!="UNKNOWN"
    @property
    def correct(self): return self.labeled and self.decision==self.truth
