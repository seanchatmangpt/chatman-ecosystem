from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Subject
from .errors import Refused
from .policy import ACTIONS
@dataclass(frozen=True, order=True)
class DecisionObservation:
    subject:Subject; policy_id:str; policy_generation:int; policy_digest:str; decision_id:str
    decision:str; truth:str; predicted_independence:Fraction; observed_at:datetime
    strategy:str; methodology:str; engine:str; region:str; evidence_root:str
    def __post_init__(self):
        if not self.decision_id or self.decision not in ACTIONS: raise Refused("REFUSED[INVALID_DECISION_OBSERVATION]")
        if self.truth not in {"INDEPENDENT","DEPENDENT"}: raise Refused("REFUSED[INVALID_TRUTH]")
        if not 0<=self.predicted_independence<=1: raise Refused("REFUSED[INVALID_PROBABILITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None: raise Refused("REFUSED[NAIVE_TIME]")
        if any(not x for x in (self.strategy,self.methodology,self.engine,self.region,self.evidence_root)): raise Refused("REFUSED[EMPTY_STRATUM_IDENTITY]")
