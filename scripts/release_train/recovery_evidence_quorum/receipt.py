import hashlib,json
SCHEMA="chatman.recovery-evidence-quorum/1"
def manufacture_receipt(payload):
    body={"schema":SCHEMA,**payload,"actuation_performed":False}
    canonical=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"digest":hashlib.sha256(canonical.encode()).hexdigest()}
def replay(receipt):
    body=receipt.get("body",{})
    if body.get("schema")!=SCHEMA or body.get("actuation_performed") is not False:return False
    payload={key:value for key,value in body.items() if key not in {"schema","actuation_performed"}}
    return manufacture_receipt(payload)["digest"]==receipt.get("digest")
