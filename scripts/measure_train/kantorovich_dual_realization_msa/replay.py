import hashlib,json
from .errors import Refused
def replay(receipt):
    b=receipt.get("body",{})
    if b.get("authority")!="OBSERVE|VERIFY": raise Refused("REFUSED[AUTHORITY_DRIFT]")
    if b.get("actuation_performed") is not False: raise Refused("REFUSED[ACTUATION_IN_MEASURE_RECEIPT]")
    raw=json.dumps(b,sort_keys=True,separators=(",",":"))
    if hashlib.sha256(raw.encode()).hexdigest()!=receipt.get("sha256"): raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"
