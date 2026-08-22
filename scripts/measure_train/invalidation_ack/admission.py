from .subject import Refused

def admit(event, deliveries, acknowledgements, discharges):
    by_delivery={d.delivery_id:d for d in deliveries}
    by_ack={a.ack_id:a for a in acknowledgements}
    seen_ack={}
    seen_discharge={}

    for d in deliveries:
        if d.event_id != event.event_id:
            raise Refused("REFUSED[FOREIGN_DELIVERY_EVENT]")
        if d.delivered_at < event.observed_at:
            raise Refused("REFUSED[DELIVERY_BEFORE_INVALIDATION]")

    for a in acknowledgements:
        d=by_delivery.get(a.delivery_id)
        if d is None:
            raise Refused("REFUSED[ORPHAN_ACKNOWLEDGEMENT]")
        if a.event_id != event.event_id or a.consumer != d.consumer or a.event_id != d.event_id:
            raise Refused("REFUSED[ACK_DELIVERY_MISMATCH]")
        if a.acknowledged_at < d.delivered_at:
            raise Refused("REFUSED[ACK_BEFORE_DELIVERY]")
        key=(a.consumer,a.event_id)
        old=seen_ack.get(key)
        if old and old != a.ack_id:
            raise Refused("REFUSED[CONTRADICTORY_ACKNOWLEDGEMENT]")
        seen_ack[key]=a.ack_id

    for x in discharges:
        a=by_ack.get(x.ack_id)
        if a is None:
            raise Refused("REFUSED[ORPHAN_DISCHARGE]")
        if x.event_id != event.event_id or x.consumer != a.consumer or x.event_id != a.event_id:
            raise Refused("REFUSED[DISCHARGE_ACK_MISMATCH]")
        if x.verified_at < a.acknowledged_at:
            raise Refused("REFUSED[DISCHARGE_BEFORE_ACK]")
        key=(x.consumer,x.event_id)
        old=seen_discharge.get(key)
        if old and old != x.result:
            raise Refused("REFUSED[CONTRADICTORY_DISCHARGE]")
        seen_discharge[key]=x.result

    return tuple(sorted(deliveries)), tuple(sorted(acknowledgements)), tuple(sorted(discharges))
