from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Calibration:
    support: int
    brier: float
    mean_gap: float
    generation: int
    digest: str

    def admitted(self, min_support=5, max_brier=0.25, max_gap=0.2):
        return self.support >= min_support and self.brier <= max_brier and self.mean_gap <= max_gap

def calibrate(observations, generation: int, digest: str):
    labeled = [o for o in observations if o.truth_independent is not None]
    if not labeled:
        raise Refused("NO_CALIBRATION_LABELS")
    actual = [
        1.0 if (o.decision.value == "INDEPENDENT") == o.truth_independent else 0.0
        for o in labeled
    ]
    predicted_correct = [1.0 - o.predicted_risk for o in labeled]
    brier = sum((p-y)**2 for p,y in zip(predicted_correct, actual))/len(labeled)
    gap = abs(sum(predicted_correct)/len(labeled) - sum(actual)/len(labeled))
    return Calibration(len(labeled), brier, gap, generation, digest)

def current(calibrations):
    cs = tuple(calibrations)
    if not cs:
        raise Refused("NO_CALIBRATION_FRONTIER")
    g = max(c.generation for c in cs)
    latest = [c for c in cs if c.generation == g]
    if len({c.digest for c in latest}) != 1:
        raise Refused("SPLIT_CALIBRATION_FRONTIER")
    return sorted(latest, key=lambda c: c.digest)[0]
