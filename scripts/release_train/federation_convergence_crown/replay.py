from .refusal import refuse
def replay(receipt,expected_digest):
    if receipt.actuation_performed:
        refuse("REPORTED_AMBIENT_ACTUATION")
    if receipt.authority!="SELECT":
        refuse("RECEIPT_AUTHORITY_DRIFT")
    if receipt.digest()!=expected_digest:
        refuse("RECEIPT_DIGEST_MISMATCH")
    return "REPLAY_MATCH"
