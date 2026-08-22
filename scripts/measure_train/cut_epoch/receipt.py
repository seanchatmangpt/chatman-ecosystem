import hashlib,json
def manufacture_receipt(consumer, cut, lease, census_rows, standing_value, parent=None):
    body={"schema":"chatman.measure-cut-epoch/1","consumer_repo":consumer.repo,"consumer_sha":consumer.sha,
          "cut_id":cut.cut_id,"cut_generation":cut.generation,
          "producer_epochs":[{"repo":e.subject.repo,"sha":e.subject.sha,"generation":e.generation,"receipt":e.receipt_sha256,"observed_at":e.observed_at.isoformat()} for e in sorted(cut.epochs)],
          "lease":{"issued_at":lease.issued_at.isoformat(),"expires_at":lease.expires_at.isoformat()},
          "census":[list(x) for x in census_rows],"standing":standing_value,"parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
