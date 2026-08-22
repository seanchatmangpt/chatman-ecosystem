import hashlib, json

def manufacture_receipt(event, impacts, standing):
    body={
        "schema":"chatman.measure-invalidation-cascade/1",
        "producer_repo":event.producer.repo,
        "producer_sha":event.producer.sha,
        "event_id":event.event_id,
        "kind":event.kind,
        "observed_at":event.observed_at.isoformat(),
        "impacts":[list(x) for x in sorted(impacts)],
        "standing":standing,
        "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
