from .subject_vector import Subject
from .evidence_axis import Axis, Outcome
from .vector import Evidence, EvidenceVector
def from_runs(repo, sha, rows, observed_at):
    subject=Subject(repo,sha)
    mapped=[]
    for name, conclusion in rows:
        axis=Axis.FOCUSED if "focused" in name.lower() or "measure" in name.lower() else Axis.REPOSITORY
        outcome={"success":Outcome.PASS,"failure":Outcome.FAIL,"queued":Outcome.PENDING,"in_progress":Outcome.PENDING}.get(conclusion,Outcome.UNKNOWN)
        mapped.append(Evidence(subject,axis,outcome,observed_at))
    return EvidenceVector(subject,tuple(mapped))
