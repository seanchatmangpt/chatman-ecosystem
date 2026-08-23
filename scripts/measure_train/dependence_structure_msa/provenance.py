from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class ProvenanceClaim:
    left_id:str
    right_id:str
    implementation_distinct:bool
    model_distinct:bool
    domain_distinct:bool
    asserted_independent:bool

def audit(claim, empirical_verdict):
    structurally_distinct=claim.implementation_distinct and claim.model_distinct and claim.domain_distinct
    if claim.asserted_independent and not structurally_distinct:
        raise Refused("REFUSED[UNPROVEN_PROVENANCE_INDEPENDENCE]")
    if claim.asserted_independent and empirical_verdict=="DEPENDENT":
        raise Refused("REFUSED[PROVENANCE_EMPIRICAL_CONTRADICTION]")
    return {
      "structurally_distinct":structurally_distinct,
      "asserted_independent":claim.asserted_independent,
      "empirical_verdict":empirical_verdict,
    }
