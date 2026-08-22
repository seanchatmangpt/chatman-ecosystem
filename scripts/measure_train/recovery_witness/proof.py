import hashlib, json
from dataclasses import dataclass
from .witness import CompatibilityWitness
from .lease import WitnessLease
from .subject import Refused

STRATEGIES={"RESELECT","REBIND_EQUIVALENT","REQUALIFY_COMPATIBLE"}

@dataclass(frozen=True, order=True)
class RecoveryProof:
    strategy: str
    witness: CompatibilityWitness | None
    lease: WitnessLease
    proof_id: str
    def __post_init__(self):
        if self.strategy not in STRATEGIES: raise Refused("REFUSED[UNKNOWN_RECOVERY_STRATEGY]")
        if not self.proof_id.strip(): raise Refused("REFUSED[EMPTY_PROOF_ID]")
        if self.strategy!="RESELECT" and self.witness is None:
            raise Refused("REFUSED[MISSING_COMPATIBILITY_WITNESS]")
        if self.strategy=="RESELECT" and self.witness is not None:
            raise Refused("REFUSED[UNNEEDED_COMPATIBILITY_WITNESS]")
    @property
    def digest(self):
        body={"strategy":self.strategy,"proof_id":self.proof_id,
              "witness_id":None if self.witness is None else self.witness.witness_id,
              "issued_at":self.lease.issued_at.isoformat(),"expires_at":self.lease.expires_at.isoformat()}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
