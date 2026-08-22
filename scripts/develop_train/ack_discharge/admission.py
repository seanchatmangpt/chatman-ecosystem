from dataclasses import dataclass
from .witness import Delivery,Acknowledgement,Discharge
class RefusedEvidence(ValueError): pass
@dataclass(frozen=True,slots=True)
class AdmittedChain: delivery:Delivery; acknowledgement:Acknowledgement; discharge:Discharge
def admit_chain(event,delivery,ack,discharge):
 if {delivery.event_id,ack.event_id,discharge.event_id}!={event.event_id}: raise RefusedEvidence('REFUSED[EVENT_MISMATCH]')
 if len({delivery.consumer.identity,ack.consumer.identity,discharge.consumer.identity})!=1: raise RefusedEvidence('REFUSED[CONSUMER_MISMATCH]')
 if not(event.occurred_at<=delivery.delivered_at<=ack.acknowledged_at<=discharge.discharged_at): raise RefusedEvidence('REFUSED[CAUSAL_ORDER]')
 if ack.delivery_receipt!=delivery.receipt: raise RefusedEvidence('REFUSED[DELIVERY_RECEIPT_MISMATCH]')
 if not discharge.acknowledgement_receipt or not discharge.evidence_receipt: raise RefusedEvidence('REFUSED[UNRECEIPTED_DISCHARGE]')
 return AdmittedChain(delivery,ack,discharge)
