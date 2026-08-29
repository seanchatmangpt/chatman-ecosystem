from dataclasses import dataclass
from . import DependencySubject, Refusal

@dataclass(frozen=True)
class DependencyObservation:
    subject: DependencySubject
    workflow: str
    conclusion: str
    observed_at: str

    def standing(self) -> str:
        if self.conclusion == 'success': return 'PARTIAL_ALIVE'
        if self.conclusion == 'failure': return 'BUILD_BROKEN'
        if self.conclusion in {'queued','in_progress','pending'}: return 'UNKNOWN'
        raise Refusal('REFUSED[UNKNOWN_WORKFLOW_CONCLUSION]')
