from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .errors import Refused


class Relation(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    EQUAL = "EQUAL"
    CONCURRENT = "CONCURRENT"


@dataclass(frozen=True)
class VectorClock:
    values: tuple[tuple[str, int], ...]

    @classmethod
    def from_dict(cls, values: dict[str, int]) -> "VectorClock":
        if not values or any(not key or value < 0 for key, value in values.items()):
            raise Refused("INVALID_VECTOR_CLOCK")
        return cls(tuple(sorted(values.items())))

    def compare(self, other: "VectorClock") -> Relation:
        left = dict(self.values)
        right = dict(other.values)
        keys = set(left) | set(right)
        le = all(left.get(k, 0) <= right.get(k, 0) for k in keys)
        ge = all(left.get(k, 0) >= right.get(k, 0) for k in keys)
        if le and ge:
            return Relation.EQUAL
        if le:
            return Relation.BEFORE
        if ge:
            return Relation.AFTER
        return Relation.CONCURRENT


def concurrent_pairs(clocks: dict[str, VectorClock]) -> int:
    names = sorted(clocks)
    return sum(
        clocks[names[i]].compare(clocks[names[j]]) == Relation.CONCURRENT
        for i in range(len(names))
        for j in range(i + 1, len(names))
    )
