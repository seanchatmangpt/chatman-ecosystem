import hashlib,json

def manufacture_receipt(subject,frontier,census,parent=None):
    body={"schema":"chatman.measure-policy-state-msa/1","repo":subject.repo,"sha":subject.sha,"frontier_revision":None if frontier is None else frontier.revision,"frontier_digest":None if frontier is None else frontier.digest,"census":census,"parent":parent,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
