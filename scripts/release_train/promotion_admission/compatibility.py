from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .evidence import Axis, Outcome

class Compatibility(str, Enum):
    COMPATIBLE="COMPATIBLE"; DIVERGED="DIVERGED"; UNKNOWN="UNKNOWN"

@dataclass(frozen=True)
class CompatibilityResult:
    state: Compatibility
    shared_axes: tuple[Axis, ...]
    divergent_axes: tuple[Axis, ...]

def compare_vectors(left: dict[Axis, Outcome], right: dict[Axis, Outcome]) -> CompatibilityResult:
    shared = tuple(sorted(set(left) & set(right), key=lambda a: a.value))
    if not shared:
        return CompatibilityResult(Compatibility.UNKNOWN, (), ())
    divergent = tuple(axis for axis in shared if left[axis] != right[axis])
    return CompatibilityResult(
        Compatibility.DIVERGED if divergent else Compatibility.COMPATIBLE,
        shared,
        divergent,
    )
