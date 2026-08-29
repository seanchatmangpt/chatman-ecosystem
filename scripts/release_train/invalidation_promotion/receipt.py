import hashlib, json
from .subject import Refusal
SCHEMA='chatman.invalidation-promotion/1'
def canonical(obj):
    return json.dumps(obj,sort_keys=True,separators=(',',':'))
def manufacture_receipt(payload):
    body={'schema':SCHEMA,'payload':payload,'actuation_performed':False}
    digest=hashlib.sha256(canonical(body).encode()).hexdigest()
    return {'body':body,'sha256':digest}
def replay_receipt(receipt):
    body=receipt.get('body',{})
    if body.get('schema')!=SCHEMA or body.get('actuation_performed') is not False:
        raise Refusal('REFUSED[RECEIPT_AUTHORITY_OR_SCHEMA]')
    actual=hashlib.sha256(canonical(body).encode()).hexdigest()
    if actual!=receipt.get('sha256'):
        raise Refusal('REFUSED[RECEIPT_MISMATCH]')
    return True
