import hashlib,json
def manufacture(subject,model,census_value,standing_value):
    body={"schema":"chatman.measure-transport-invariance-realization/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"model_generation":model.generation,"model_digest":model.digest,"census":census_value,"standing":standing_value,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":")); return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
