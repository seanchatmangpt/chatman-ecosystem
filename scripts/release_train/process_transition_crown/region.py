from dataclasses import dataclass
from datetime import datetime, timezone
from .refusal import Refused

@dataclass(frozen=True)
class RegionWitness:
    host: str
    region: str
    semantic_digest: str
    runtime_version: str
    cert_fingerprint: str
    observed_at: datetime
    encrypted: bool


def require_current(witnesses: tuple[RegionWitness,...], now: datetime, max_age_seconds: int):
    if len({w.host for w in witnesses}) < 2 or len({w.region for w in witnesses}) < 2:
        raise Refused("INSUFFICIENT_REGION_INDEPENDENCE")
    if len({w.semantic_digest for w in witnesses}) != 1:
        raise Refused("REGION_SEMANTIC_DIVERGENCE")
    for w in witnesses:
        if not w.encrypted or not w.cert_fingerprint:
            raise Refused("REGION_TLS_UNPROVEN")
        age=(now.astimezone(timezone.utc)-w.observed_at.astimezone(timezone.utc)).total_seconds()
        if age < 0 or age > max_age_seconds:
            raise Refused("REGION_WITNESS_STALE")
    return witnesses
