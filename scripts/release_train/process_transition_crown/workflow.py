from dataclasses import dataclass
from .subject import SubjectEpoch
from .obligation import State
from .refusal import Refused

@dataclass(frozen=True)
class WorkflowResult:
    head_sha: str
    name: str
    conclusion: str

    def state_for(self, subject: SubjectEpoch) -> State:
        if self.head_sha != subject.sha:
            raise Refused("WORKFLOW_FOREIGN_HEAD")
        c=self.conclusion.lower()
        if c in {"queued","in_progress","pending","requested","waiting"}: return State.UNKNOWN
        if c=="success": return State.ALIVE
        if c in {"failure","cancelled","timed_out","action_required"}: return State.BUILD_BROKEN
        return State.UNKNOWN
