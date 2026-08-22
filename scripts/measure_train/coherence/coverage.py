from dataclasses import dataclass
from enum import Enum
from .obligation import Obligation
from .scope import satisfies_scope
from .witness import Witness, Outcome

class CoverageState(str, Enum): SATISFIED="SATISFIED"; FAILED="FAILED"; PENDING="PENDING"; UNKNOWN="UNKNOWN"; UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True)
class Coverage:
    obligation: Obligation
    state: CoverageState
    witness_count: int

def cover(obligations: list[Obligation], witnesses: list[Witness]):
    result=[]
    for o in obligations:
        matched=[w for w in witnesses if w.axis==o.axis and satisfies_scope(w.scope,o.scope)]
        outcomes={w.outcome for w in matched}
        if Outcome.FAIL in outcomes: state=CoverageState.FAILED
        elif Outcome.PENDING in outcomes: state=CoverageState.PENDING
        elif Outcome.PASS in outcomes: state=CoverageState.SATISFIED
        elif matched and outcomes=={Outcome.UNSUPPORTED}: state=CoverageState.UNSUPPORTED
        else: state=CoverageState.UNKNOWN
        result.append(Coverage(o,state,len(matched)))
    return tuple(sorted(result,key=lambda c:c.obligation.obligation_id))
