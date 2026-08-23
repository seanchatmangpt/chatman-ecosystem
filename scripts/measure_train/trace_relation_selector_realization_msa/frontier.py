from dataclasses import dataclass
from .selector import SelectorIdentity
from .subject import Refused

@dataclass(frozen=True, order=True)
class CalibrationFrontier:
    selector: SelectorIdentity
    calibration_digest: str
    state: str

    def __post_init__(self):
        if len(self.calibration_digest)!=64 or any(c not in "0123456789abcdef" for c in self.calibration_digest):
            raise Refused("REFUSED[INVALID_CALIBRATION_DIGEST]")
        if self.state not in {"INSUFFICIENT","CALIBRATED","UNRELIABLE"}:
            raise Refused("REFUSED[INVALID_CALIBRATION_STATE]")

def current_frontier(rows):
    by={}
    for row in rows:
        key=row.selector.selector
        previous=by.get(key)
        if previous is None or row.selector.generation>previous.selector.generation:
            by[key]=row
        elif row.selector.generation==previous.selector.generation and row.calibration_digest!=previous.calibration_digest:
            raise Refused("REFUSED[DIVERGENT_SELECTOR_FRONTIER]")
    return tuple(sorted(by.values(), key=lambda r:r.selector.selector.value))
