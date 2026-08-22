from dataclasses import dataclass
import hashlib, json

SCHEMA="chatman.release-realized-policy-admission/1"

@dataclass(frozen=True)
class Receipt:
    body: dict
    digest: str

def issue(body):
    material=dict(body)
    material.update({"schema":SCHEMA,"authority":"SELECT","actuation_performed":False})
    digest=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Receipt(material,digest)

def replay(receipt):
    if receipt.body.get("schema")!=SCHEMA or receipt.body.get("authority")!="SELECT" or receipt.body.get("actuation_performed") is not False:
        return False
    expected=hashlib.sha256(json.dumps(receipt.body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return expected==receipt.digest
