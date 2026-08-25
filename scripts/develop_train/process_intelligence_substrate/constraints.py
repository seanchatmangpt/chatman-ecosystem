from __future__ import annotations
from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True, order=True)
class Precedence:
    before: str
    after: str


def validate_precedence(trace: tuple[str, ...], rules: tuple[Precedence, ...]) -> bool:
    positions: dict[str, int] = {}
    for i, activity in enumerate(trace):
        positions.setdefault(activity, i)
    for rule in rules:
        if rule.before == rule.after:
            raise Refused("REFLEXIVE_PRECEDENCE", rule.before)
        if rule.after in positions and (rule.before not in positions or positions[rule.before] > positions[rule.after]):
            return False
    return True
