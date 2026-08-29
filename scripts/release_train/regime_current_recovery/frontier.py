from dataclasses import dataclass
from .regime import CalibrationRegime
from .subject import Refusal, Subject

@dataclass(frozen=True)
class RegimeFrontier:
    current: CalibrationRegime
    historical: tuple[CalibrationRegime,...]

def build_frontier(subject: Subject, source_id: str, regimes: list[CalibrationRegime]) -> RegimeFrontier:
    matching=[r for r in regimes if r.model.subject==subject and r.model.source_id==source_id]
    if not matching: raise Refusal('REFUSED[EMPTY_REGIME_FRONTIER]')
    max_generation=max(r.generation for r in matching)
    maxima=[r for r in matching if r.generation==max_generation]
    if len(maxima)!=1: raise Refusal('REFUSED[DIVERGENT_REGIME_FRONTIER]')
    current=maxima[0]
    historical=tuple(sorted((r for r in matching if r is not current),key=lambda r:(r.generation,r.model.window.until)))
    return RegimeFrontier(current,historical)
