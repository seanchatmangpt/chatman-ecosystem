from dataclasses import dataclass
from .errors import Refused
from .provenance import Provenance
@dataclass(frozen=True)
class ValidatorWitness:
    validator_id: str
    oracle_digest: str
    provenance: Provenance
    evidence_id: str
    def __post_init__(self):
        if not self.validator_id or len(self.oracle_digest)!=64 or not self.evidence_id:
            raise Refused("INVALID_VALIDATOR")
def require_distinct_validators(a,b):
    if a.validator_id==b.validator_id or a.oracle_digest==b.oracle_digest:
        raise Refused("VALIDATOR_ALIAS")
    return True
