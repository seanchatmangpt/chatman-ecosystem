import hashlib,json
def manufacture(subject,census_rows,standing_value):
    body={"schema":"chatman.measure-pi-projection-qualification/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"generation":subject.generation,"census":[list(x) for x in census_rows],"standing":standing_value,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":")); return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
