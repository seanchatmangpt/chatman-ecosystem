from dataclasses import dataclass,asdict
import hashlib,json
from .errors import Refused
@dataclass(frozen=True)
class Receipt:
    subject:str; calibration_generation:int; calibration_digest:str; decision:str; composition_mode:str; standing:str; blockers:tuple=(); authority:str='SELECT'; phases:tuple=('VERIFY','CONSTRUCT'); actuation_performed:bool=False; digest_sha256:str=''
def _body(r):
    d=asdict(r);d.pop('digest_sha256',None);return d
def manufacture(**kwargs):
    r=Receipt(**kwargs); body=json.dumps(_body(r),sort_keys=True,separators=(',',':')).encode(); return Receipt(**_body(r),digest_sha256=hashlib.sha256(body).hexdigest())
def replay(r):
    if r.actuation_performed: raise Refused('RECEIPT_REPORTS_ACTUATION')
    expected=manufacture(**_body(r))
    if expected.digest_sha256!=r.digest_sha256: raise Refused('RECEIPT_MISMATCH')
    return True
