from dataclasses import dataclass
import hashlib, json
@dataclass(frozen=True)
class Receipt:
    schema:str
    payload:dict
    digest:str
def _canon(schema,payload): return json.dumps({"schema":schema,"payload":payload},sort_keys=True,separators=(",",":")).encode()
def manufacture(payload:dict)->Receipt:
    body=dict(payload)
    body["actuation_performed"]=False
    schema="chatman.consumer-promotion/1"
    return Receipt(schema,body,hashlib.sha256(_canon(schema,body)).hexdigest())
def replay(receipt:Receipt)->bool:
    if receipt.schema!="chatman.consumer-promotion/1": return False
    if receipt.payload.get("actuation_performed") is not False:return False
    return hashlib.sha256(_canon(receipt.schema,receipt.payload)).hexdigest()==receipt.digest
