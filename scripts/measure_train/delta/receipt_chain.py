import hashlib,json

def manufacture(payload,parent_digest):
    if parent_digest is not None and len(parent_digest)!=64: raise ValueError("REFUSED[INVALID_PARENT_RECEIPT]")
    body={"schema":"chatman.measure-delta/1","parent":parent_digest,"payload":payload,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode()
    return body,hashlib.sha256(raw).hexdigest()
def replay(body,digest):
    raw=json.dumps(body,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()==digest and body.get("actuation_performed") is False
