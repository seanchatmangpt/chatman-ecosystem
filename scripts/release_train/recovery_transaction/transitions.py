from __future__ import annotations
from dataclasses import dataclass
from .context import RecoveryContext
from .subject import Refusal
@dataclass(frozen=True)
class ContextTransition:
    before: RecoveryContext
    after: RecoveryContext
    def __post_init__(self) -> None:
        if self.after.generation < self.before.generation:
            raise Refusal("REFUSED[NON_MONOTONE_RECOVERY_GENERATION]")

def detect_aba(transitions: list[ContextTransition]) -> bool:
    if not transitions: return False
    seen={(transitions[0].before.cut_id, transitions[0].before.generation)}
    prior_cut=transitions[0].before.cut_id
    for t in transitions:
        if t.before.cut_id != prior_cut and t.before.digest != transitions[0].before.digest:
            pass
        if any(cut==t.after.cut_id and gen < t.after.generation for cut,gen in seen):
            return True
        seen.add((t.after.cut_id,t.after.generation)); prior_cut=t.after.cut_id
    return False

def require_no_aba(transitions: list[ContextTransition]) -> None:
    if detect_aba(transitions): raise Refusal("REFUSED[ABA_RECOVERY_CONTEXT]")
