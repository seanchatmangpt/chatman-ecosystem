import hashlib,json
def manufacture(subject, frontier, standing_value):
    body={"schema":"chatman.measure-robustness-bound-msa/1","repo":subject.repo,"sha":subject.sha,
          "frontier":[{"estimator":m.estimator,"generation":m.generation,"digest":m.digest,"state":m.state} for m in sorted(frontier)],
          "standing":standing_value,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
