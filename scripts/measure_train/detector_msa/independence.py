import hashlib
from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True, order=True)
class DetectorSource:
    detector_id: str
    family: str
    implementation_digest: str
    runtime_digest: str
    def __post_init__(self):
        for value in (self.detector_id, self.family, self.implementation_digest, self.runtime_digest):
            if not value:
                raise Refused("REFUSED[INCOMPLETE_DETECTOR_SOURCE]")
    @property
    def fingerprint(self):
        raw = "|".join((self.detector_id, self.family, self.implementation_digest, self.runtime_digest))
        return hashlib.sha256(raw.encode()).hexdigest()

def relation(a: DetectorSource, b: DetectorSource, explicit_independent=frozenset()):
    pair = frozenset((a.fingerprint, b.fingerprint))
    if a.fingerprint == b.fingerprint or a.implementation_digest == b.implementation_digest:
        return "SAME_EVIDENCE"
    if pair in explicit_independent and a.family != b.family and a.runtime_digest != b.runtime_digest:
        return "INDEPENDENT"
    if a.family == b.family or a.runtime_digest == b.runtime_digest:
        return "CORRELATED"
    return "UNKNOWN"
