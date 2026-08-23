import hashlib,json
def manufacture(subject,model,status,metrics):
    body={"schema":"chatman.measure-decision-realization-transport/1","repo":subject.repo,"sha":subject.sha,
          "semantic_digest":subject.semantic_digest,"model":{"source":model.source,"target":model.target,"generation":model.generation,"digest":model.digest},
          "metrics":metrics,"standing":status,"authority":"OBSERVE|VERIFY","actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
