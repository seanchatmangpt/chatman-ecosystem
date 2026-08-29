from __future__ import annotations

from dataclasses import dataclass
from .frontier import Frontier, standing
from .obligation import Obligation, coverage

@dataclass(frozen=True)
class Admission:
    subject: str
    standing: str
    obligation_states: tuple[tuple[str,str], ...]
    promotable: bool
    reasons: tuple[str,...]

def admit_subject(subject: str, frontier: Frontier, obligations: tuple[Obligation,...]) -> Admission:
    states=coverage(frontier, obligations)
    state=standing(frontier)
    reasons=[]
    for ob in obligations:
        value=states[ob.obligation_id]
        if ob.required and value != "PASS": reasons.append(f"{ob.obligation_id}:{value}")
    if state != "PARTIAL_ALIVE": reasons.append(f"standing:{state}")
    return Admission(subject=subject, standing=state, obligation_states=tuple(sorted(states.items())), promotable=not reasons, reasons=tuple(sorted(reasons)))
