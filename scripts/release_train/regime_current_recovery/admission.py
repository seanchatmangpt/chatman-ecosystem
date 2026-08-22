import hashlib
from .evidence import RecoveryWitness
from .frontier import RegimeFrontier
from .regime import RegimeState
from .subject import Refusal

def model_digest(frontier: RegimeFrontier) -> str:
    model=frontier.current.model
    payload='|'.join((model.subject.exact,model.source_id,str(frontier.current.generation),str(model.support),str(model.tpr),str(model.fpr),str(model.brier)))
    return hashlib.sha256(payload.encode()).hexdigest()

def admit_current(witness: RecoveryWitness, frontier: RegimeFrontier, now) -> None:
    current=frontier.current
    if witness.subject!=current.model.subject or witness.source_id!=current.model.source_id: raise Refusal('REFUSED[FOREIGN_REGIME_WITNESS]')
    if witness.observed_at>now: raise Refusal('REFUSED[FUTURE_EVIDENCE]')
    if witness.regime_generation!=current.generation or witness.model_digest!=model_digest(frontier): raise Refusal('REFUSED[STALE_CALIBRATION_REGIME]')
    if current.state==RegimeState.DRIFT: raise Refusal('REFUSED[CALIBRATION_DRIFTED]')
    if current.state==RegimeState.INSUFFICIENT: raise Refusal('REFUSED[CALIBRATION_UNDER_SUPPORTED]')
