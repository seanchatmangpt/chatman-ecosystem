from dataclasses import dataclass
from datetime import datetime
from .evidence import ObligationEvidence
from .subject import SubjectEpoch, Refused

@dataclass(frozen=True)
class WorkflowObservation:
    run_id: str
    head_sha: str
    name: str
    status: str
    conclusion: str | None
    observed_at: datetime

def workflow_to_evidence(epoch: SubjectEpoch, obligation_id: str, row: WorkflowObservation):
    if row.head_sha != epoch.subject.sha:
        raise Refused("REFUSED[FOREIGN_WORKFLOW_HEAD]")
    if row.status != "completed":
        state = "PENDING"
    elif row.conclusion == "success":
        state = "PASS"
    elif row.conclusion in {"failure","cancelled","timed_out","action_required"}:
        state = "FAIL"
    else:
        state = "UNKNOWN"
    return ObligationEvidence(
        epoch=epoch,
        obligation_id=obligation_id,
        source_id=f"github-actions:{row.run_id}:{row.name}",
        state=state,
        observed_at=row.observed_at,
    )
