from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class RegionWitness:
    host: str
    region: str
    encrypted: bool
    certificate_digest: str
    generation: int

def require_multi_region_tls(witnesses: list[RegionWitness], generation: int) -> tuple[str,...]:
    current=[w for w in witnesses if w.generation==generation]
    if any(not w.encrypted for w in current): raise Refused("PLAINTEXT_REGION_EVIDENCE")
    if any(len(w.certificate_digest)!=64 for w in current): raise Refused("INVALID_TLS_CERTIFICATE_DIGEST")
    if len({w.host for w in current}) < 2 or len({w.region for w in current}) < 2:
        raise Refused("INSUFFICIENT_MULTI_REGION_TLS")
    return tuple(sorted(w.region for w in current))
