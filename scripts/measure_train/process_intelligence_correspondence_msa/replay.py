import hashlib,json
from .subject import Refused
def replay(r):
    b=r.get("body",{})
    if b.get("authority")!="OBSERVE|VERIFY": raise Refused("REFUSED[AUTHORITY_DRIFT]")
    if b.get("actuation_performed") is not False: raise Refused("REFUSED[MEASUREMENT_ACTUATION]")
    raw=json.dumps(b,sort_keys=True,separators=(",",":"))
    if hashlib.sha256(raw.encode()).hexdigest()!=r.get("sha256"): raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"
