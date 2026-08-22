from .frontier import current_witness_frontier
from .admission import admit_recovery
from .contradiction import contradictions
from .standing import standing
from .receipt import manufacture_receipt

def qualify(consumer, before, after, proof, witnesses, now, parent_receipt=None):
    frontier=current_witness_frontier(witnesses)
    conflicts=contradictions(frontier)
    admission=admit_recovery(proof,before,after,frontier,now)
    status=standing((proof,),conflicts)
    receipt=manufacture_receipt(consumer,before,after,proof,admission,status,parent_receipt)
    telemetry={"activity":"measure_recovery_witness","consumer_repo":consumer.repo,
               "consumer_sha":consumer.sha,"before":before.digest,"after":after.digest,
               "strategy":proof.strategy,"witness_id":None if proof.witness is None else proof.witness.witness_id,
               "standing":status,"actuation_performed":False}
    return {"frontier":frontier,"contradictions":conflicts,"admission":admission,
            "standing":status,"receipt":receipt,"telemetry":telemetry,
            "actuation_performed":False}
