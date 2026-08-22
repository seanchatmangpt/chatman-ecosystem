from .frontier import current_cut_frontier
from .admission import admit_cut
from .census import cut_census,standing
from .receipt import manufacture_receipt
from .telemetry import project
def qualify(consumer,cuts,supersessions,lease,current_epochs,observations,now,parent_receipt=None):
    current=current_cut_frontier(cuts,supersessions)
    target=next((c for c in cuts if c.cut_id==lease.cut_id),None)
    if target is None:
        from .subject import Refused
        raise Refused("REFUSED[UNKNOWN_LEASED_CUT]")
    admission=admit_cut(target,lease,current,current_epochs,now)
    rows=cut_census(observations); status=standing(rows)
    receipt=manufacture_receipt(consumer,target,lease,rows,status,parent_receipt)
    return {"admission":admission,"cut":target,"census":rows,"standing":status,"receipt":receipt,
            "telemetry":project(consumer,target,rows),"actuation_performed":False}
