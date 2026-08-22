import json, hashlib

def manufacture_receipt(subject, coverage, chain, parent=None):
    body={"schema":"chatman.measure-provenance/1","repo":subject.repo,"sha":subject.sha,
          "coverage":coverage,"chain":chain,"parent":parent,"actuation_performed":False}
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"sha256":hashlib.sha256(raw.encode()).hexdigest()}
