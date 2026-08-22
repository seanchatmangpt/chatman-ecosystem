from .admission import admit_claim
from .drift import classify_drift
from .receipt import manufacture_receipt

def qualify(claim, current_producer, observed_scope, now):
    drift=classify_drift(claim,current_producer,now)
    admission=admit_claim(claim,current_producer,observed_scope,now)
    standing = "BUILD_BROKEN" if current_producer.standing=="BUILD_BROKEN" else (
        "BLOCKED" if current_producer.standing=="BLOCKED" else
        "UNKNOWN" if current_producer.standing in {"UNKNOWN","UNSUPPORTED"} else
        "PARTIAL_ALIVE"
    )
    receipt=manufacture_receipt(claim,drift,admission)
    return {"drift":drift,"admission":admission,"standing":standing,
            "receipt":receipt,"actuation_performed":False}
