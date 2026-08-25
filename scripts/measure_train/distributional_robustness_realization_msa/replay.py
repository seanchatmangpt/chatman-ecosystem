import hashlib,json
from .refusal import Refused
def replay(receipt):
    body=receipt.get("body",{})
    if body.get("authority")!="OBSERVE|VERIFY": raise Refused("REFUSED[AUTHORITY_DRIFT]")
    if body.get("actuation_performed") is not False: raise Refused("REFUSED[ACTUATION_IN_MEASUREMENT_RECEIPT]")
    raw=json.dumps(body,sort_keys=True,separators=(",",":"))
    if hashlib.sha256(raw.encode()).hexdigest()!=receipt.get("sha256"): raise Refused("REFUSED[RECEIPT_MISMATCH]")
    return "REPLAY_MATCH"
