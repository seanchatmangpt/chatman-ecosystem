from dataclasses import dataclass
from datetime import datetime
from .state import PolicyState
from .subject import Refused
OUTCOMES={"COMMITTED","CAS_REFUSED","CORRUPTION_REFUSED","IO_FAILURE"}
@dataclass(frozen=True, order=True)
class Transition:
    before: PolicyState
    after: PolicyState | None
    expected_revision: int
    expected_digest: str
    outcome: str
    issued_at: datetime
    completed_at: datetime
    writer_id: str
    event_id: str
    def __post_init__(self):
        if self.outcome not in OUTCOMES: raise Refused("REFUSED[INVALID_TRANSITION_OUTCOME]")
        if self.issued_at.tzinfo is None or self.completed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TRANSITION_TIME]")
        if self.completed_at < self.issued_at: raise Refused("REFUSED[REVERSED_TRANSITION_INTERVAL]")
        if not self.writer_id or not self.event_id: raise Refused("REFUSED[EMPTY_TRANSITION_ID]")
