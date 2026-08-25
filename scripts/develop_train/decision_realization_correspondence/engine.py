import hashlib
import json
from dataclasses import dataclass
from .admission import admit
from .calibration import calibrate
from .drift import Cusum
from .methodologies import require_methodologies
from .realized_loss import mean_loss
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    standing: str
    receipt: Receipt | None
    mean_realized_loss: object
    calibration_gap: object
    drifted: bool

def _digest(policy, observations):
    payload={
        "policy": policy.policy_id,
        "generation": policy.generation,
        "observations": sorted(o.observation_id for o in observations),
    }
    return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",", ":")).encode()).hexdigest()

def qualify(subject, policy, observations, dependency_standings=()):
    xs=admit(policy, observations)
    require_methodologies(o.methodology for o in xs)
    if "BUILD_BROKEN" in dependency_standings:
        return Qualification("BUILD_BROKEN",None,mean_loss(policy,xs),None,False)
    if "BLOCKED" in dependency_standings:
        return Qualification("BLOCKED",None,mean_loss(policy,xs),None,False)
    calibration=calibrate(xs)
    c=Cusum()
    for o in xs:
        realized=1 if (o.truth is not None and o.decision!=o.truth) else 0
        c=c.update(realized,o.predicted_risk)
    standing="PARTIAL_ALIVE" if calibration.admitted and not c.changed else "UNKNOWN"
    receipt=Receipt(subject.key,policy.generation,standing,_digest(policy,xs)) if standing=="PARTIAL_ALIVE" else None
    return Qualification(standing,receipt,mean_loss(policy,xs),calibration.gap,c.changed)
