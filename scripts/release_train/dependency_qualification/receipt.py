import hashlib, json
from . import Refusal

def canonical(payload): return json.dumps(payload, sort_keys=True, separators=(',',':'))
def manufacture(payload: dict) -> dict:
    body={'schema':'chatman.dependency-qualification/1','payload':payload,'actuation_performed':False}
    body['digest']='sha256:'+hashlib.sha256(canonical(body).encode()).hexdigest()
    return body
def replay(receipt: dict) -> None:
    if receipt.get('schema')!='chatman.dependency-qualification/1' or receipt.get('actuation_performed') is not False:
        raise Refusal('REFUSED[RECEIPT_SCHEMA_OR_AUTHORITY]')
    supplied=receipt.get('digest',''); body=dict(receipt); body.pop('digest',None)
    expected='sha256:'+hashlib.sha256(canonical(body).encode()).hexdigest()
    if supplied != expected: raise Refusal('REFUSED[RECEIPT_TAMPER]')
