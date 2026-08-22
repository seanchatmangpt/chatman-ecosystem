from __future__ import annotations
from dataclasses import dataclass
from .cut import EvidenceCut
from .identity import Refusal
@dataclass(frozen=True, slots=True)
class CutFrontier:
    cuts: tuple[EvidenceCut, ...]
    def current(self) -> tuple[EvidenceCut, ...]:
        if not self.cuts: raise Refusal("REFUSED[EMPTY_CUT_FRONTIER]")
        generation = max(c.generation for c in self.cuts)
        current = tuple(c for c in self.cuts if c.generation == generation)
        if len({c.cut_id for c in current}) != len(current): raise Refusal("REFUSED[DUPLICATE_CURRENT_CUT_ID]")
        return tuple(sorted(current, key=lambda c: c.cut_id))
