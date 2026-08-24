from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .primal import solve_primal
from .dual import derive_dual
from .certificate import verify_certificate
@dataclass(frozen=True)
class WassersteinAmbiguity:
    center: object
    radius: Fraction
    metric: object
    def __post_init__(self):
        if self.radius < 0:
            raise Refused("NEGATIVE_AMBIGUITY_RADIUS")
    def certificate(self, candidate):
        plan = solve_primal(self.center, candidate, self.metric)
        dual = derive_dual(plan, self.center, candidate, self.metric)
        return verify_certificate(self.center, candidate, self.metric, plan, dual)
    def contains(self, candidate):
        return self.certificate(candidate).primal_value <= self.radius
