from .errors import Refused
def replay(receipt,expected):
    if receipt.digest!=expected: raise Refused("RECEIPT_DIGEST_MISMATCH")
    if receipt.actuation_performed: raise Refused("REPORTED_AMBIENT_ACTUATION")
    return "REPLAY_MATCH"
