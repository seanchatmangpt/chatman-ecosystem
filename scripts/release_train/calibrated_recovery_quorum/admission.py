from datetime import timezone
from .subject import Refused

def admit_witness(witness, source, model, now, min_trials=6):
    if witness.source_fingerprint != source.fingerprint: raise Refused("REFUSED[WITNESS_SOURCE_MISMATCH]")
    if model.source_id != source.fingerprint: raise Refused("REFUSED[CALIBRATION_SOURCE_MISMATCH]")
    if witness.utc() > now.astimezone(timezone.utc): raise Refused("REFUSED[FUTURE_EVIDENCE]")
    if model.support < min_trials: return {"admitted":False,"reason":"UNDER_CALIBRATED","support":model.support}
    return {"admitted":True,"reason":"CALIBRATED","support":model.support}
