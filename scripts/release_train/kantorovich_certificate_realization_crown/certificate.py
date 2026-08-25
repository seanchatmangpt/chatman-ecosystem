from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class Certificate:
    digest: str
    generation: int
    primal: Fraction
    dual: Fraction
    feasibility_residual: Fraction = Fraction(0)
    slackness_residual: Fraction = Fraction(0)
    def validate(self):
        if len(self.digest) != 64 or any(c not in '0123456789abcdef' for c in self.digest):
            raise Refused("INVALID_CERTIFICATE_DIGEST")
        if self.generation < 0:
            raise Refused("INVALID_CERTIFICATE_GENERATION")
        if min(self.primal, self.dual, self.feasibility_residual, self.slackness_residual) < 0:
            raise Refused("NEGATIVE_CERTIFICATE_QUANTITY")
        return self
