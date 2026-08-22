from __future__ import annotations
from dataclasses import dataclass
from .context import RecoveryContext
from .subject import Refusal

@dataclass(frozen=True)
class Transition:
    before: RecoveryContext
    after: RecoveryContext

def detect_aba(transitions: list[Transition]) -> bool:
    if len(transitions) < 2:
        return False
    first = transitions[0].before
    seen: dict[str, tuple[int, str]] = {first.cut_id: (first.generation, first.digest)}
    for transition in transitions:
        key = transition.after.cut_id
        fingerprint = (transition.after.generation, transition.after.digest)
        if key in seen and seen[key] != fingerprint:
            return True
        seen[key] = fingerprint
    return False

def refuse_aba(transitions: list[Transition]) -> None:
    if detect_aba(transitions):
        raise Refusal("ABA_RECOVERY_CONTEXT", "cut identifier recurred with changed generation/context")
