from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DriftWitness:
    previous_digest: str
    current_digest: str

    @property
    def drifted(self) -> bool:
        return self.previous_digest != self.current_digest


def methodology_drift(previous: dict[str, str], current: dict[str, str]) -> tuple[DriftWitness, ...]:
    keys = sorted(set(previous) | set(current))
    return tuple(DriftWitness(previous.get(k, ""), current.get(k, "")) for k in keys if previous.get(k, "") != current.get(k, ""))
