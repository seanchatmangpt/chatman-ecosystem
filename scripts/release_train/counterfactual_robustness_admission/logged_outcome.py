from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .refusal import refuse

@dataclass(frozen=True)
class LoggedOutcome:
    evidence_id: str
    behavior_propensity: Fraction
    target_propensity: Fraction
    reward: Fraction
    model_prediction: Fraction|None
    observed_at: datetime
    def __post_init__(self):
        if not self.evidence_id or self.observed_at.tzinfo is None: refuse("INVALID_LOGGED_OUTCOME")
        if not (0 < self.behavior_propensity <= 1): refuse("POSITIVITY_VIOLATION")
        if not (0 <= self.target_propensity <= 1): refuse("INVALID_TARGET_PROPENSITY")
        if not (0 <= self.reward <= 1): refuse("INVALID_REWARD")
        if self.model_prediction is not None and not (0 <= self.model_prediction <= 1): refuse("INVALID_MODEL_PREDICTION")

def admit_log(rows):
    rows=tuple(rows)
    if not rows: refuse("EMPTY_LOG")
    ids=[r.evidence_id for r in rows]
    if len(ids)!=len(set(ids)): refuse("DUPLICATE_EVIDENCE")
    return rows
