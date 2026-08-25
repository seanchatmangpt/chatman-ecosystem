from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from .identity import Subject, digest64
from .refusal import require

_CERT=re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class RegionWitness:
    subject: Subject
    host: str
    region: str
    runtime_version: str
    cert_fingerprint: str
    semantic_digest: str
    observed_at: datetime
    latency_ms: int
    loss_ppm: int

    def __post_init__(self):
        require(self.host and self.region and self.runtime_version, "INEXACT_REGION_IDENTITY")
        require(bool(_CERT.fullmatch(self.cert_fingerprint)), "INVALID_CERT_FINGERPRINT")
        digest64(self.semantic_digest)
        require(self.semantic_digest == self.subject.semantic_digest, "REGION_DIGEST_DIVERGENCE")
        require(self.observed_at.tzinfo is not None, "NAIVE_REGION_TIME")
        require(self.latency_ms >= 0 and 0 <= self.loss_ppm <= 1_000_000, "INVALID_NETWORK_METRIC")

def require_multi_region(rows, now: datetime, max_age: timedelta, max_latency_ms: int, max_loss_ppm: int):
    require(now.tzinfo is not None, "NAIVE_NOW")
    require(len({r.host for r in rows}) >= 2 and len({r.region for r in rows}) >= 2, "INSUFFICIENT_REGION_INDEPENDENCE")
    require(len({r.semantic_digest for r in rows})==1, "REGION_DIGEST_SPLIT")
    for r in rows:
        require(r.observed_at <= now and now-r.observed_at <= max_age, "STALE_REGION_WITNESS")
        require(r.latency_ms <= max_latency_ms, "LATENCY_BUDGET_EXCEEDED")
        require(r.loss_ppm <= max_loss_ppm, "LOSS_BUDGET_EXCEEDED")
    return True
