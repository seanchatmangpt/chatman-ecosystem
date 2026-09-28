import hashlib,json
def stable_id(kind,payload):
 return kind+":sha256:"+hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()
