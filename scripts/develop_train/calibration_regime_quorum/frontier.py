from __future__ import annotations
from dataclasses import dataclass
from .regime import CalibrationRegime
from .subject import Refusal
@dataclass(frozen=True,slots=True)
class RegimeFrontier:
    current:CalibrationRegime
    historical:tuple[CalibrationRegime,...]
def build_frontier(regimes:tuple[CalibrationRegime,...])->RegimeFrontier:
    if not regimes: raise Refusal("REFUSED[EMPTY_REGIME_FRONTIER]")
    if len({r.source_id for r in regimes})!=1: raise Refusal("REFUSED[MIXED_REGIME_SOURCES]")
    maximum=max(r.generation for r in regimes); current=[r for r in regimes if r.generation==maximum]
    if len(current)!=1:
        if len({(r.state,r.model) for r in current})!=1: raise Refusal("REFUSED[DIVERGENT_REGIME_FRONTIER]")
        current=[current[0]]
    cur=current[0]
    return RegimeFrontier(cur,tuple(sorted((r for r in regimes if r is not cur),key=lambda r:r.generation)))
