from __future__ import annotations
from dataclasses import dataclass
from .cut import EvidenceCut
from .strategy import CutStrategy, score_cut
@dataclass(frozen=True, slots=True)
class StrategyComparison:
    cut_id: str
    latest_complete: tuple[int, ...]
    max_freshness: tuple[int, ...]
    min_skew: tuple[int, ...]
def compare_cut(cut: EvidenceCut) -> StrategyComparison:
    return StrategyComparison(cut.cut_id, score_cut(cut, CutStrategy.LATEST_COMPLETE).score, score_cut(cut, CutStrategy.MAX_FRESHNESS).score, score_cut(cut, CutStrategy.MIN_SKEW).score)
def pareto_frontier(cuts: tuple[EvidenceCut, ...]) -> tuple[str, ...]:
    rows = {c.cut_id: compare_cut(c) for c in cuts}; winners: list[str] = []
    for cut_id, row in rows.items():
        metrics = (row.latest_complete[0], row.max_freshness[0], row.min_skew[0])
        dominated = False
        for other_id, other in rows.items():
            if other_id == cut_id: continue
            om = (other.latest_complete[0], other.max_freshness[0], other.min_skew[0])
            if all(a >= b for a, b in zip(om, metrics)) and any(a > b for a, b in zip(om, metrics)):
                dominated = True; break
        if not dominated: winners.append(cut_id)
    return tuple(sorted(winners))
