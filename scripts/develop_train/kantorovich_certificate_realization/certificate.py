from dataclasses import dataclass
import re
from fractions import Fraction
from .errors import Refused

_HEX = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class Certificate:
    certificate_digest: str
    generation: int
    primal_value: Fraction
    dual_value: Fraction
    max_dual_violation: Fraction
    max_slackness_residual: Fraction

    def __post_init__(self) -> None:
        if not _HEX.fullmatch(self.certificate_digest):
            raise Refused("INVALID_CERTIFICATE_DIGEST")
        if self.generation < 0:
            raise Refused("INVALID_CERTIFICATE_GENERATION")
        if min(self.primal_value, self.dual_value, self.max_dual_violation, self.max_slackness_residual) < 0:
            raise Refused("NEGATIVE_CERTIFICATE_QUANTITY")

    @property
    def gap(self) -> Fraction:
        return abs(self.primal_value - self.dual_value)
