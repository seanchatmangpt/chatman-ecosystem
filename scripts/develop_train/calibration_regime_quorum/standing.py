from __future__ import annotations
from dataclasses import dataclass
from .decision import SequentialDecision
_FAILURES={"BUILD_BROKEN","BLOCKED"}
@dataclass(frozen=True,slots=True)
class StandingResult:
    standing:str; blockers:tuple[str,...]
def bounded_standing(*,decision:SequentialDecision,independent_clusters:int,required_clusters:int,outcomes:tuple[str,...],dependency_standings:dict[str,str])->StandingResult:
    blockers=tuple(sorted(name for name,standing in dependency_standings.items() if standing in _FAILURES))
    if blockers: return StandingResult("BLOCKED",blockers)
    if "FAIL" in outcomes or decision.result=="REJECT": return StandingResult("BUILD_BROKEN",())
    if decision.result!="ACCEPT_BOUNDED" or independent_clusters<required_clusters: return StandingResult("UNKNOWN",())
    return StandingResult("PARTIAL_ALIVE",())
