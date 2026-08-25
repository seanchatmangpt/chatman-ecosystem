from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True, slots=True)
class LoggedOutcome:
    case_id:str; action:str; reward:Fraction; behavior_p:Fraction; target_p:Fraction; model_prediction:Fraction|None=None
    def __post_init__(self):
        if not self.case_id or not self.action: raise Refused('REFUSED_EVIDENCE_IDENTITY')
        if not (0 < self.behavior_p <= 1 and 0 <= self.target_p <= 1): raise Refused('REFUSED_PROPENSITY_DOMAIN')
        if self.model_prediction is not None and not (0 <= self.model_prediction <= 1): raise Refused('REFUSED_MODEL_PREDICTION_DOMAIN')
def admit_log(rows):
    rows=tuple(rows)
    if not rows: raise Refused('REFUSED_EMPTY_LOG')
    ids=[r.case_id for r in rows]
    if len(ids)!=len(set(ids)): raise Refused('REFUSED_DUPLICATE_CASE')
    return rows
