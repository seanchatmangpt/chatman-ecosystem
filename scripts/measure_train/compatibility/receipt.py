import hashlib, json
def make_receipt(subject, standing, axes, parent=None):
    body={"schema":"chatman.measure-vector/1","repo":subject.repo,"sha":subject.sha,"standing":standing,"axes":sorted(axes),"parent":parent,"actuation_performed":False}
    canonical=json.dumps(body,sort_keys=True,separators=(",",":"))
    return {"body":body,"digest":hashlib.sha256(canonical.encode()).hexdigest()}
