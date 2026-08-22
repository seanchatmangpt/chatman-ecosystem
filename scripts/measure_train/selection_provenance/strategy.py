import hashlib
import json
from dataclasses import dataclass, field
from .subject import Refused

STRATEGIES = {"LATEST_COMPLETE", "MAX_FRESHNESS", "MIN_SKEW"}

@dataclass(frozen=True)
class StrategyBinding:
    name: str
    policy_digest: str
    parameters: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self):
        if self.name not in STRATEGIES:
            raise Refused("REFUSED[UNKNOWN_SELECTION_STRATEGY]")
        if len(self.policy_digest) != 64 or any(c not in "0123456789abcdef" for c in self.policy_digest):
            raise Refused("REFUSED[INVALID_POLICY_DIGEST]")
        keys = [k for k, _ in self.parameters]
        if len(keys) != len(set(keys)):
            raise Refused("REFUSED[DUPLICATE_STRATEGY_PARAMETER]")

    @property
    def fingerprint(self):
        body = {"name": self.name, "policy_digest": self.policy_digest,
                "parameters": sorted([list(x) for x in self.parameters])}
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode()).hexdigest()
