from .errors import Refused
def replay(receipt,expected_digest):
    if receipt.actuation_performed: raise Refused('REFUSED[REPORTED_AMBIENT_ACTUATION]')
    if receipt.digest()!=expected_digest: raise Refused('REFUSED[RECEIPT_DRIFT]')
    return 'REPLAY_MATCH'
