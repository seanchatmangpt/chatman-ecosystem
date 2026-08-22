from .frontier import current_frontier
from .admission import admit_cut
from .coherence import detect_torn_cut
from .census import census
from .standing import standing
from .receipt import manufacture_receipt

def qualify(consumer, epochs, cut, observations, parent_receipt=None):
    frontier=current_frontier(epochs)
    admitted=admit_cut(cut,frontier,observations)
    torn=detect_torn_cut(cut,admitted)
    rows=census(admitted)
    status=standing(rows,torn)
    receipt=manufacture_receipt(consumer,cut,rows,status,parent_receipt)
    telemetry=tuple({
        "activity":"measure_consistent_cut",
        "consumer_repo":consumer.repo,
        "consumer_sha":consumer.sha,
        "producer_repo":obs.producer_epoch.subject.repo,
        "producer_sha":obs.producer_epoch.subject.sha,
        "generation":obs.producer_epoch.generation,
        "scope":obs.scope,
        "outcome":obs.outcome,
        "evidence_id":obs.evidence_id,
        "time":obs.observed_at.isoformat(),
    } for obs in admitted)
    return {"frontier":frontier,"census":rows,"standing":status,"receipt":receipt,
            "telemetry":telemetry,"actuation_performed":False}
