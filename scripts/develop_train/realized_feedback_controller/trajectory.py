from dataclasses import dataclass
from .errors import Refused
from .realization import StepRealization

@dataclass(frozen=True)
class Trajectory:
    steps: tuple[StepRealization, ...]

    def __post_init__(self):
        if not self.steps:
            raise Refused("REFUSED_EMPTY_TRAJECTORY")
        seen=set()
        for expected, step in enumerate(self.steps):
            if step.step != expected:
                raise Refused("REFUSED_NONCONTIGUOUS_TRAJECTORY")
            if step.evidence_id in seen:
                raise Refused("REFUSED_DUPLICATE_EVIDENCE")
            seen.add(step.evidence_id)
        if any(a.observed_at > b.observed_at for a,b in zip(self.steps, self.steps[1:])):
            raise Refused("REFUSED_TIME_REGRESSION")

    @property
    def residuals(self):
        return tuple(s.residual for s in self.steps)
