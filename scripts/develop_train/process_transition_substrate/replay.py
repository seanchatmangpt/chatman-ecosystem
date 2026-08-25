from .receipt import Receipt
from .errors import Refused
def replay(receipt:Receipt, expected_digest:str):
    actual=receipt.digest()
    if actual != expected_digest: raise Refused("REFUSED[REPLAY_DIGEST_MISMATCH]")
    return "REPLAY_MATCH"
