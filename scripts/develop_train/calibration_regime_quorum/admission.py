from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .frontier import RegimeFrontier
from .subject import Refusal,Subject
_OUTCOMES={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
@dataclass(frozen=True,slots=True)
class RecoveryWitness:
    subject:Subject; source_id:str; outcome:str; observed_at:datetime; regime_generation:int
    def __post_init__(self)->None:
        if self.outcome not in _OUTCOMES: raise Refusal("REFUSED[INVALID_WITNESS_OUTCOME]")
        if self.observed_at.tzinfo is None: raise Refusal("REFUSED[NAIVE_WITNESS_TIME]")
def admit_witness(witness:RecoveryWitness,frontier:RegimeFrontier,*,now:datetime)->None:
    if witness.observed_at>now: raise Refusal("REFUSED[FUTURE_RECOVERY_WITNESS]")
    regime=frontier.current
    if witness.source_id!=regime.source_id: raise Refusal("REFUSED[WITNESS_SOURCE_MISMATCH]")
    if witness.regime_generation!=regime.generation: raise Refusal("REFUSED[STALE_CALIBRATION_REGIME]")
    if regime.state=="DRIFT": raise Refusal("REFUSED[CALIBRATION_DRIFTED]")
    if regime.state=="INSUFFICIENT" or regime.model is None: raise Refusal("REFUSED[INSUFFICIENT_CURRENT_CALIBRATION]")
