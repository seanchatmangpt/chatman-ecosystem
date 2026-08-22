from datetime import datetime
from .admission import admit
from .candidate import select
from .graph import topo, propagate
from .receipt import manufacture
def manufacture_plan(*,claim,evidence,current_receipt,current_schema,now:datetime,deps,standing,candidates):
    a=admit(claim,evidence,current_receipt,current_schema,now)
    if not a.admitted: raise ValueError(a.reason)
    order=topo(deps)
    propagated=propagate(order,standing,deps)
    if propagated.get(claim.producer.key) not in {"ALIVE","PARTIAL_ALIVE"}:
        raise ValueError("BLOCKED[DEPENDENCY_CLOSURE]")
    chosen=select(candidates)
    plan={"phases":["VERIFY","CONSTRUCT"],"consumer":claim.consumer.key,"producer":claim.producer.key,
          "receipt":claim.receipt,"schema":claim.schema,"dependency_order":order,"candidate":chosen.name,
          "standing":"PARTIAL_ALIVE"}
    return plan, manufacture(plan)
