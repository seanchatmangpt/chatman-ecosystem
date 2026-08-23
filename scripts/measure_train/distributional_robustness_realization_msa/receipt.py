import hashlib,json
def manufacture(subject,models,census_rows,standing_value):
    body={"schema":"chatman.measure-distributional-robustness-realization/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"generation":subject.generation,"models":[{"kind":m.kind,"radius":[m.radius.numerator,m.radius.denominator],"generation":m.generation,"digest":m.digest,"ground_metric_digest":m.ground_metric_digest} for m in models],"census":list(census_rows),"standing":standing_value,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
