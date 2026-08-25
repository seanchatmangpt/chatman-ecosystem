import hashlib,json
def manufacture(subject, calibration, status):
    body={"schema":"chatman.measure-kantorovich-dual-realization/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"support":calibration.support,"state":calibration.state,"standing":status,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
