import hashlib,json

def manufacture(subject,census,standing_value,parent=None):
    body={"schema":"chatman.measure-process-intelligence-closure/1","repo":subject.repo,"sha":subject.sha,
          "census":census,"standing":standing_value,"parent":parent,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),default=list)
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
