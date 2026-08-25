from __future__ import annotations
from dataclasses import dataclass
from itertools import combinations
from .event import Event
from .refusal import Refused

@dataclass(frozen=True)
class Independence:
    pairs: frozenset[frozenset[str]]

    @classmethod
    def from_pairs(cls, pairs: list[tuple[str, str]]) -> "Independence":
        normalized = set()
        for a, b in pairs:
            if not a or not b or a == b:
                raise Refused("INVALID_INDEPENDENCE_PAIR")
            normalized.add(frozenset((a, b)))
        return cls(frozenset(normalized))

    def independent(self, a: Event, b: Event) -> bool:
        return frozenset((a.object_id, b.object_id)) in self.pairs

    def all_independent(self, events: tuple[Event, ...]) -> bool:
        return all(self.independent(a, b) for a, b in combinations(events, 2))
