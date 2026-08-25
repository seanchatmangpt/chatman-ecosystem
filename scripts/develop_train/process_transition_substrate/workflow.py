from dataclasses import dataclass
from .errors import Refused
from .obligation import State
@dataclass(frozen=True)
class WorkflowResult:
    head_sha:str
    conclusion:str|None
def adapt(result:WorkflowResult, expected_sha:str):
    if result.head_sha != expected_sha: raise Refused("REFUSED[FOREIGN_WORKFLOW_HEAD]")
    c=(result.conclusion or "").lower()
    return {"success":State.PASS,"failure":State.FAIL,"cancelled":State.UNKNOWN,"skipped":State.UNKNOWN}.get(c,State.UNKNOWN)
