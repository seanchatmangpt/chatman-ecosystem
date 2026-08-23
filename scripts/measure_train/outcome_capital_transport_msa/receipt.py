import hashlib,json
def manufacture(subject,standing_value,census,parent=None):
    body={"schema":"chatman.measure-outcome-capital-transport/1","repo":subject.repo,"sha":subject.sha,
          "semantic_digest":subject.semantic_digest,"census":census,"standing":standing_value,"parent":parent,
          "authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
