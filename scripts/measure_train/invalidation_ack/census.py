def acknowledgement_census(event, affected, deliveries, acknowledgements, discharges):
    delivered={(d.consumer,d.event_id) for d in deliveries}
    acked={(a.consumer,a.event_id) for a in acknowledgements}
    discharge={(x.consumer,x.event_id):x.result for x in discharges}
    rows=[]
    for consumer,depth in sorted(affected):
        key=(consumer,event.event_id)
        if key not in delivered:
            state="PENDING_DELIVERY"
        elif key not in acked:
            state="PENDING_ACK"
        elif key not in discharge:
            state="PENDING_DISCHARGE"
        elif discharge[key] == "REQUALIFIED":
            state="REQUALIFIED"
        elif discharge[key] == "BLOCKED":
            state="BLOCKED"
        else:
            state="UNSUPPORTED"
        rows.append((consumer,depth,state))
    return tuple(rows)
