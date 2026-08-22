import hashlib
import json
from dataclasses import dataclass
from .subject import Refused

KINDS = {"WINDOW_L1", "PREQUENTIAL_CUSUM", "MINIMAX_CURRENT"}

@dataclass(frozen=True)
class DetectorPolicy:
    detector_id: str
    kind: str
    generation: int
    parameters: tuple[tuple[str, str], ...]

    def __post_init__(self):
        if not self.detector_id or self.kind not in KINDS or self.generation < 0:
            raise Refused("REFUSED[INVALID_DETECTOR_POLICY]")
        keys = [key for key, _ in self.parameters]
        if len(keys) != len(set(keys)):
            raise Refused("REFUSED[DUPLICATE_POLICY_PARAMETER]")

    @property
    def fingerprint(self):
        body = {"detector_id": self.detector_id, "kind": self.kind, "generation": self.generation, "parameters": sorted(self.parameters)}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()
