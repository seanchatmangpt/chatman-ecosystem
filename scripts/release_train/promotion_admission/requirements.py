from __future__ import annotations
from dataclasses import dataclass
from .evidence import Axis, Outcome

class RequirementRefusal(ValueError):
    pass

@dataclass(frozen=True)
class ReleaseProfile:
    name: str
    required_axes: frozenset[Axis]
    accepted: frozenset[Outcome] = frozenset({Outcome.PASS})

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.required_axes:
            raise RequirementRefusal("REFUSED[INVALID_RELEASE_PROFILE]")
        if Outcome.FAIL in self.accepted or Outcome.PENDING in self.accepted:
            raise RequirementRefusal("REFUSED[UNSAFE_RELEASE_OUTCOME_POLICY]")

def evaluate_profile(vector: dict[Axis, Outcome], profile: ReleaseProfile) -> tuple[bool, tuple[Axis, ...]]:
    missing = tuple(sorted(profile.required_axes - set(vector), key=lambda a: a.value))
    if missing:
        return False, missing
    return all(vector[a] in profile.accepted for a in profile.required_axes), ()
