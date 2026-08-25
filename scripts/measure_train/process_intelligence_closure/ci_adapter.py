from datetime import datetime
from .evidence import RailEvidence
from .subject import Subject,Refused

def workflow_observation(subject: Subject, rail: str, engine: str, semantic_digest: str, run: dict, observed_at: datetime):
    run_id=run.get("id")
    status=run.get("status")
    conclusion=run.get("conclusion")
    if not isinstance(run_id,int) or run_id <= 0: raise Refused("REFUSED[INVALID_WORKFLOW_RUN_ID]")
    if status=="completed":
        if conclusion=="success": outcome="PASS"
        elif conclusion is None: outcome="UNKNOWN"
        else: outcome="FAIL"
    elif status in {"queued","in_progress","waiting","requested","pending"}: outcome="PENDING"
    else: outcome="UNKNOWN"
    return RailEvidence(subject,rail,engine,semantic_digest,outcome,f"workflow:{run_id}",observed_at)
