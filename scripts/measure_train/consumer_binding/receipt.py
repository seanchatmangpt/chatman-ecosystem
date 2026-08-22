import hashlib, json

def manufacture_receipt(claim, drift_state, admission_state):
    body = {
        "schema":"chatman.measure-consumer-binding/1",
        "consumer_repo":claim.consumer.subject.repo,
        "consumer_sha":claim.consumer.subject.sha,
        "component":claim.consumer.component,
        "producer_repo":claim.producer.subject.repo,
        "producer_sha":claim.producer.subject.sha,
        "producer_receipt":claim.producer.receipt_sha256,
        "producer_schema":claim.producer.schema,
        "required_scope":claim.required_scope,
        "lease_issued_at":claim.lease.issued_at.isoformat(),
        "lease_expires_at":claim.lease.expires_at.isoformat(),
        "drift":drift_state,
        "admission":admission_state,
        "actuation_performed":False,
    }
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
