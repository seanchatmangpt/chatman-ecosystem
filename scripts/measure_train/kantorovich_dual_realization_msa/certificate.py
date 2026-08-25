from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Certificate:
    primal: Fraction
    dual: Fraction
    max_dual_violation: Fraction
    max_slackness_violation: Fraction
    plan_digest: str
    dual_digest: str
    def __post_init__(self):
        if len(self.plan_digest)!=64 or len(self.dual_digest)!=64: raise Refused("REFUSED[INVALID_CERTIFICATE_DIGEST]")
    @property
    def gap(self): return self.primal-self.dual
