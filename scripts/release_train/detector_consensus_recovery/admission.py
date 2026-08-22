from dataclasses import dataclass
from .frontier import unique_current

@dataclass(frozen=True)
class AdmittedVote:
    vote: object
    calibration: object

def admit_votes(votes, generations):
    current=unique_current(generations); admitted=[]; seen=set()
    for v in votes:
        fp=v.detector.fingerprint
        if fp in seen: raise ValueError("REFUSED[DUPLICATE_DETECTOR_VOTE]")
        seen.add(fp); g=current.get(fp)
        if g is None: raise ValueError("REFUSED[NO_CURRENT_CALIBRATION]")
        if v.calibration_generation!=g.generation: raise ValueError("REFUSED[STALE_CALIBRATION_GENERATION]")
        if v.calibration_fingerprint!=g.calibration.detector_fingerprint: raise ValueError("REFUSED[FOREIGN_CALIBRATION]")
        if g.calibration.state!="CALIBRATED": raise ValueError(f"REFUSED[DETECTOR_{g.calibration.state}]")
        admitted.append(AdmittedVote(v,g.calibration))
    return tuple(admitted)
