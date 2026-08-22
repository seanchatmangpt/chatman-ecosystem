from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True)
class CalibrationCohort:
    epochs:tuple
    required_sources:frozenset
    def __post_init__(self):
        sources=[e.source for e in self.epochs]
        if len(sources)!=len(set(sources)): raise Refused("REFUSED[DUPLICATE_COHORT_SOURCE]")
        if set(sources)!=set(self.required_sources): raise Refused("REFUSED[INCOMPLETE_COHORT]")
    def by_source(self): return {e.source:e for e in self.epochs}
