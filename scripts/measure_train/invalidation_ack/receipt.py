import hashlib, json

def manufacture_receipt(event, census, standing_value, parent=None):
    rows=[{"consumer_repo":c.repo,"consumer_sha":c.sha,"depth":depth,"state":state} for c,depth,state in census]
    body={
        "schema":"chatman.measure-invalidation-ack/1",
        "producer_repo":event.producer.repo,
        "producer_sha":event.producer.sha,
        "event_id":event.event_id,
        "kind":event.kind,
        "observed_at":event.observed_at.isoformat(),
        "census":rows,
        "standing":standing_value,
        "parent":parent,
        "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
