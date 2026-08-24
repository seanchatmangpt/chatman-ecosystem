from .errors import Refused


def replay(receipt, expected_digest: str) -> str:
    if receipt.digest != expected_digest:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    if receipt.actuation_performed:
        raise Refused("REPORTED_AMBIENT_ACTUATION")
    if receipt.authority == "DO":
        raise Refused("RECEIPT_AUTHORITY_DRIFT")
    return "REPLAY_MATCH"
