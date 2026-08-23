from dataclasses import dataclass, asdict
import hashlib, json
from .refusal import Refused

@dataclass(frozen=True)
class Receipt:
    subject: str
    strategy: str
    selected: tuple[str,...]
    standing: str
    blockers: tuple[str,...]
    authority: str="SELECT"
    phases: tuple[str,...]=("VERIFY","CONSTRUCT")
    actuation_performed: bool=False
    @property
    def body(self): return asdict(self)
    @property
    def digest(self): return hashlib.sha256(json.dumps(self.body,sort_keys=True,separators=(",",":"),default=list).encode()).hexdigest()

def replay(receipt: Receipt, digest: str) -> bool:
    if receipt.actuation_performed: raise Refused("RECEIPT_REPORTS_ACTUATION")
    if receipt.digest != digest: raise Refused("RECEIPT_MISMATCH")
    return True
