from .frontier import canonical_frontier
from .admission import admit
from .standing import standing
from .receipt import manufacture_receipt
from .telemetry import project

def qualify(proof, policy, candidates, outcomes, parent_receipt=None):
    frontier,digest=canonical_frontier(candidates)
    selected=admit(proof,policy,frontier,digest)
    status=standing(outcomes)
    receipt=manufacture_receipt(proof,selected,status,parent_receipt)
    return {"selected":selected,"standing":status,"receipt":receipt,
            "telemetry":project(proof,policy,selected,digest),"actuation_performed":False}
