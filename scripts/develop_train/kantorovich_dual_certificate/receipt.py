from dataclasses import dataclass
import hashlib, json
from .errors import Refused
def _canon(value): return json.dumps(value, sort_keys=True, separators=(",", ":"))
@dataclass(frozen=True)
class Receipt:
    subject: str; standing: str; primal_digest: str; dual_digest: str; certificate_digest: str; authority: str = "VERIFY"; actuation_performed: bool = False
    def __post_init__(self):
        if self.actuation_performed:
            raise Refused("REPORTED_AMBIENT_ACTUATION")
        if self.authority not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}:
            raise Refused("INVALID_RECEIPT_AUTHORITY")
    @property
    def body(self):
        return {"schema":"chatman.develop-kantorovich-dual-certificate/1","subject":self.subject,"standing":self.standing,"primal_digest":self.primal_digest,"dual_digest":self.dual_digest,"certificate_digest":self.certificate_digest,"authority":self.authority,"actuation_performed":self.actuation_performed}
    @property
    def digest(self): return hashlib.sha256(_canon(self.body).encode()).hexdigest()
def replay(receipt, expected):
    if receipt.digest != expected:
        raise Refused("RECEIPT_DIGEST_MISMATCH")
    if receipt.actuation_performed:
        raise Refused("REPORTED_AMBIENT_ACTUATION")
    return "REPLAY_MATCH"
