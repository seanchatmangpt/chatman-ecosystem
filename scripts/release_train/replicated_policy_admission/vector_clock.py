from dataclasses import dataclass
from enum import Enum
from .refusal import Refused

class Relation(str, Enum):
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    EQUAL = "EQUAL"
    CONCURRENT = "CONCURRENT"

@dataclass(frozen=True)
class VectorClock:
    values: tuple[tuple[str, int], ...]

    @classmethod
    def from_dict(cls, raw: dict[str, int]) -> "VectorClock":
        if not raw or any(not k or not isinstance(v, int) or v < 0 for k, v in raw.items()):
            raise Refused("INVALID_VECTOR_CLOCK")
        return cls(tuple(sorted(raw.items())))

    def as_dict(self) -> dict[str, int]:
        return dict(self.values)

    def compare(self, other: "VectorClock") -> Relation:
        keys = set(self.as_dict()) | set(other.as_dict())
        a, b = self.as_dict(), other.as_dict()
        le = all(a.get(k, 0) <= b.get(k, 0) for k in keys)
        ge = all(a.get(k, 0) >= b.get(k, 0) for k in keys)
        if le and ge: return Relation.EQUAL
        if le: return Relation.BEFORE
        if ge: return Relation.AFTER
        return Relation.CONCURRENT

    def join(self, other: "VectorClock") -> "VectorClock":
        keys = set(self.as_dict()) | set(other.as_dict())
        a, b = self.as_dict(), other.as_dict()
        return VectorClock.from_dict({k: max(a.get(k, 0), b.get(k, 0)) for k in keys})
