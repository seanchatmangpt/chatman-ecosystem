import hashlib,json
def manufacture(subject,census_value,standing_value):
    body={"schema":"chatman.measure-process-intelligence-correspondence/1","repo":subject.repo,"sha":subject.sha,"census":census_value,"standing":standing_value,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
