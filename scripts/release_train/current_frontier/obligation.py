from __future__ import annotations

from dataclasses import dataclass
from .frontier import Frontier

class Refusal(ValueError):
    pass

_SCOPE_RANK={"FOCUSED":1,"RUNTIME":2,"REPOSITORY":3,"DEPENDENCY":3,"RECEIPT":2}

@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    required_scope: str
    required: bool = True

def coverage(frontier: Frontier, obligations: tuple[Obligation, ...]) -> dict[str,str]:
    result={}
    for ob in obligations:
        candidates=[e for e in frontier.current if _SCOPE_RANK.get(e.scope,0) >= _SCOPE_RANK.get(ob.required_scope,99)]
        if not candidates:
            result[ob.obligation_id]="MISSING" if ob.required else "OPTIONAL_MISSING"
            continue
        outcomes={e.outcome for e in candidates}
        if "FAIL" in outcomes: result[ob.obligation_id]="FAIL"
        elif "PENDING" in outcomes or "UNKNOWN" in outcomes: result[ob.obligation_id]="UNKNOWN"
        elif outcomes == {"UNSUPPORTED"}: result[ob.obligation_id]="UNSUPPORTED"
        elif "PASS" in outcomes: result[ob.obligation_id]="PASS"
        else: result[ob.obligation_id]="UNKNOWN"
    return result

def require_complete(states: dict[str,str], obligations: tuple[Obligation,...]) -> None:
    required={o.obligation_id for o in obligations if o.required}
    bad={k:v for k,v in states.items() if k in required and v != "PASS"}
    if bad:
        raise Refusal(f"REFUSED[INCOMPLETE_CURRENT_FRONTIER]:{sorted(bad.items())}")
