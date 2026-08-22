import hashlib,json
from .subject import Refusal
SCHEMA='chatman.promotion-recovery/1'
def canonical(body): return json.dumps(body,sort_keys=True,separators=(',',':'))
def manufacture(body):
    payload={'schema':SCHEMA,**body,'actuation_performed':False}
    digest=hashlib.sha256(canonical(payload).encode()).hexdigest()
    return {'payload':payload,'digest':digest}
def replay(receipt):
    p=receipt.get('payload',{})
    if p.get('schema')!=SCHEMA: raise Refusal('REFUSED[RECEIPT_SCHEMA]')
    if p.get('actuation_performed') is not False: raise Refusal('REFUSED[RECEIPT_AUTHORITY_DRIFT]')
    expected=hashlib.sha256(canonical(p).encode()).hexdigest()
    if expected!=receipt.get('digest'): raise Refusal('REFUSED[RECEIPT_MISMATCH]')
    return True
