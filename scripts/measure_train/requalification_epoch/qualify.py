from .admission import admit_witness
from .census import census
from .standing import standing
from .receipt import manufacture_receipt

def qualify(epoch,consumers,witnesses,parent_receipt=None):
    admitted=[]
    for w in sorted(witnesses,key=lambda x:(x.observed_at,x.kind,x.witness_id)):
        admit_witness(epoch,w,admitted)
        admitted.append(w)
    rows=census(consumers,epoch,tuple(admitted))
    status=standing(rows)
    receipt=manufacture_receipt(epoch,rows,status,parent_receipt)
    telemetry=tuple({"activity":"requalification_epoch","producer_repo":epoch.producer.repo,"producer_sha":epoch.producer.sha,"generation":epoch.generation,"event_id":epoch.event_id,"consumer_repo":r[0],"consumer_sha":r[1],"state":r[2]} for r in rows)
    return {"census":rows,"standing":status,"receipt":receipt,"telemetry":telemetry,"actuation_performed":False}
