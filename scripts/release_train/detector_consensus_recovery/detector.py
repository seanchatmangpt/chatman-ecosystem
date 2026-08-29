from dataclasses import dataclass
from hashlib import sha256
import json

FAMILIES={"CUSUM","PAGE_HINKLEY","EWMA","WINDOW_L1","MINIMAX_CURRENT"}

@dataclass(frozen=True, order=True)
class DetectorIdentity:
    name: str
    family: str
    implementation_domain: str
    policy: tuple
    def __post_init__(self):
        if not self.name or self.family not in FAMILIES or not self.implementation_domain:
            raise ValueError("REFUSED[INVALID_DETECTOR_IDENTITY]")
    @property
    def fingerprint(self):
        body={"name":self.name,"family":self.family,"domain":self.implementation_domain,"policy":list(self.policy)}
        return sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
