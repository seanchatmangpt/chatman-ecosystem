from dataclasses import dataclass
import hashlib
import json
from .support import require
from .geometry import tv
from .weights import make, require_ess
from .estimators import sn
from .calibration import current
from .currentness import stable
from .methodology import require as require_methods
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    standing: str
    risk: float
    shift: float
    ess: float
    receipt: Receipt | None

def qualify(subject, source, target, losses, calibrations, cusum, methods, dependencies=(), max_shift=0.35, min_ess=2, strategy="MINIMAX"):
    hard = next((item for item in dependencies if item in {"BUILD_BROKEN", "BLOCKED"}), None)
    if hard:
        return Qualification(hard, float("inf"), float("inf"), 0, None)
    require_methods(methods)
    require(source, target)
    shift = tv(source, target)
    weights = require_ess(make(source, target, 10), min_ess)
    risk = sn(losses, weights)
    calibration = current(calibrations)
    standing = "PARTIAL_ALIVE" if shift <= max_shift and stable(calibration, cusum) else "UNSUPPORTED"
    payload = {"subject": subject.key, "source": source.mass, "target": target.mass, "risk": round(risk, 12), "shift": round(shift, 12), "ess": round(weights.ess, 12), "calibration": calibration.digest}
    evidence = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return Qualification(standing, risk, shift, weights.ess, Receipt(subject.key, strategy, standing, evidence))
