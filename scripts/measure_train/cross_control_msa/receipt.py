import hashlib,json
def manufacture(subject,result_digest,capital,status):
 body={"schema":"chatman.measure-cross-control-composition/1","repo":subject.repo,"sha":subject.sha,"semantic_digest":subject.semantic_digest,"generation":subject.generation,"result_digest":result_digest,"effective_capital":capital,"standing":status,"authority":"OBSERVE|VERIFY","actuation_performed":False}
 raw=json.dumps(body,sort_keys=True,separators=(",",":"))
 return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
