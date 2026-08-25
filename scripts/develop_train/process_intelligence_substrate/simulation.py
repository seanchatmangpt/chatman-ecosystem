from __future__ import annotations
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Transition:
    source: str
    activity: str
    target: str


def simulate(initial: str, transitions: tuple[Transition, ...], plan: tuple[str, ...], max_steps: int) -> tuple[str, tuple[str, ...]]:
    if max_steps <= 0:
        raise Refused("SIMULATION_BOUND")
    table = {(t.source, t.activity): t.target for t in transitions}
    state = initial; executed: list[str] = []
    for activity in plan:
        if len(executed) >= max_steps:
            raise Refused("SIMULATION_EXHAUSTED")
        key = (state, activity)
        if key not in table:
            raise Refused("INVALID_TRANSITION", f"{state}:{activity}")
        state = table[key]; executed.append(activity)
    return state, tuple(executed)
