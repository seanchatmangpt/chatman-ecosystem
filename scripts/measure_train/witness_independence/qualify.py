from .admission import admit
from .census import cluster_census
from .diversity import diversity_vector
from .standing import evaluate
from .receipt import manufacture_receipt

def qualify(subject, observations, edges, policy, now, parent_receipt=None):
    admitted=admit(subject,observations,edges,now)
    census=cluster_census(admitted,edges)
    diversity=diversity_vector(admitted)
    status=evaluate(census,policy)
    receipt=manufacture_receipt(subject,census,diversity,status,policy,parent_receipt)
    telemetry=tuple({
        "activity":"measure_witness_independence",
        "repo":subject.repo,
        "sha":subject.sha,
        "evidence_id":o.evidence_id,
        "producer":o.source.producer,
        "source_kind":o.source.kind,
        "scope":o.scope,
        "outcome":o.outcome,
        "time":o.observed_at.isoformat(),
    } for o in admitted)
    return {"admitted":admitted,"census":census,"diversity":diversity,
            "standing":status,"receipt":receipt,"telemetry":telemetry,
            "actuation_performed":False}
