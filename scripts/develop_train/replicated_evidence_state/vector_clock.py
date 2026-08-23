from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class VectorClock:
    entries: tuple[tuple[str, int], ...]

    @classmethod
    def from_dict(cls, values: dict[str, int]):
        if not values or any(not k or v < 0 for k, v in values.items()):
            raise Refused("INVALID_VECTOR_CLOCK")
        return cls(tuple(sorted(values.items())))

    def as_dict(self):
        return dict(self.entries)

    def compare(self, other: "VectorClock") -> str:
        a, b = self.as_dict(), other.as_dict()
        keys = set(a) | set(b)
        le = all(a.get(k, 0) <= b.get(k, 0) for k in keys)
        ge = all(a.get(k, 0) >= b.get(k, 0) for k in keys)
        if le and ge: return "EQUAL"
        if le: return "BEFORE"
        if ge: return "AFTER"
        return "CONCURRENT"

    def increment(self, replica: str) -> "VectorClock":
        d = self.as_dict(); d[replica] = d.get(replica, 0) + 1
        return VectorClock.from_dict(d)

    @staticmethod
    def join(*clocks: "VectorClock") -> "VectorClock":
        if not clocks: raise Refused("EMPTY_CLOCK_JOIN")
        out = {}
        for c in clocks:
            for k, v in c.entries: out[k] = max(out.get(k, 0), v)
        return VectorClock.from_dict(out)
