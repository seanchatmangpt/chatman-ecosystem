from .frontier import current_frontier
from .admission import admit
from .fusion import fuse
from .consensus import consensus
from .standing import bounded_standing
from .receipt import manufacture_receipt
from .telemetry import project
def qualify(subject,sensors,calibrations,proof_pairs,dependencies=(),parent_receipt=None):
    frontier=current_frontier(sensors)
    admitted=admit(frontier,calibrations,frontier)
    fused=fuse(admitted)
    con=consensus(admitted,proof_pairs)
    standing=bounded_standing(fused["state"],dependencies)
    receipt=manufacture_receipt(subject,frontier,fused,con,standing,parent_receipt)
    return {"frontier":frontier,"fusion":fused,"consensus":con,"standing":standing,
            "receipt":receipt,"telemetry":project(subject,frontier,admitted,fused,standing),
            "actuation_performed":False}
