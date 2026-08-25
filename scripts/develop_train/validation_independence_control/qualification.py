from dataclasses import dataclass
from .methodology import require_methodologies
from .failure import require_failure_worlds
@dataclass(frozen=True)
class Qualification:
    standing: str
    blockers: tuple[str,...]
def combine_standing(states):
    states=set(states)
    if "BUILD_BROKEN" in states: return "BUILD_BROKEN"
    if "BLOCKED" in states: return "BLOCKED"
    if "UNKNOWN" in states: return "UNKNOWN"
    return "PARTIAL_ALIVE"
def qualify(*,methodologies,failure_worlds,dependency_states):
    require_methodologies(methodologies); require_failure_worlds(failure_worlds)
    standing=combine_standing(dependency_states)
    return Qualification(standing, tuple(sorted(s for s in dependency_states if s!="PARTIAL_ALIVE")))
