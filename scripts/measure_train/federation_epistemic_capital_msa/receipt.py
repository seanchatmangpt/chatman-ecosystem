import hashlib,json
def manufacture(subject,capital,calibration,status):
    body={"schema":"chatman.measure-federation-epistemic-capital/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"nominal":capital.nominal,"effective_n":round(capital.effective_n,12),"duplication_ratio":round(capital.duplication_ratio,12),"calibration":calibration.state,"standing":status,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":")); return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
