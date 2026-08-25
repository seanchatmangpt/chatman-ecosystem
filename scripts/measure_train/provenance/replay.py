import json, hashlib
from .subject import Refused

def replay(receipt):
    raw=json.dumps(receipt["body"],sort_keys=True,separators=(",",":"))
    got=hashlib.sha256(raw.encode()).hexdigest()
    if got != receipt.get("sha256"): raise Refused("REFUSED[RECEIPT_MISMATCH]")
    if receipt["body"].get("actuation_performed") is not False: raise Refused("REFUSED[ACTUATION_IN_MEASUREMENT_RECEIPT]")
    return "REPLAY_MATCH"
