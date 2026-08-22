from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .cut import EvidenceCut
from .identity import Refusal
class CutStrategy(str, Enum):
    LATEST_COMPLETE = "LATEST_COMPLETE"
    MAX_FRESHNESS = "MAX_FRESHNESS"
    MIN_SKEW = "MIN_SKEW"
@dataclass(frozen=True, slots=True)
class CutScore:
    cut_id: str
    strategy: CutStrategy
    score: tuple[int, ...]
def score_cut(cut: EvidenceCut, strategy: CutStrategy) -> CutScore:
    gens = tuple(e.generation for e in cut.epochs)
    if not gens: raise Refusal("REFUSED[EMPTY_CUT]")
    freshness = sum(gens); skew = max(gens) - min(gens)
    if strategy is CutStrategy.LATEST_COMPLETE: score = (cut.generation, freshness, -skew)
    elif strategy is CutStrategy.MAX_FRESHNESS: score = (freshness, cut.generation, -skew)
    elif strategy is CutStrategy.MIN_SKEW: score = (-skew, freshness, cut.generation)
    else: raise Refusal("REFUSED[UNKNOWN_CUT_STRATEGY]")
    return CutScore(cut.cut_id, strategy, score)
def select_cut(cuts: tuple[EvidenceCut, ...], strategy: CutStrategy) -> EvidenceCut:
    if not cuts: raise Refusal("REFUSED[NO_CUT_CANDIDATES]")
    return max(cuts, key=lambda c: (score_cut(c, strategy).score, c.cut_id))
