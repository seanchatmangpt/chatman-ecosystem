from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
KINDS={"TV","HELLINGER","W1","CHI_SQUARE"}
@dataclass(frozen=True, order=True)
class AmbiguityModel:
    kind: str
    radius: Fraction
    generation: int
    digest: str
    ground_metric_digest: str|None=None
    def __post_init__(self):
        if self.kind not in KINDS: raise Refused("REFUSED[UNKNOWN_AMBIGUITY_KIND]")
        if self.radius < 0: raise Refused("REFUSED[NEGATIVE_RADIUS]")
        if self.generation < 0 or len(self.digest)!=64: raise Refused("REFUSED[INVALID_AMBIGUITY_MODEL]")
        if self.kind=="W1" and (self.ground_metric_digest is None or len(self.ground_metric_digest)!=64): raise Refused("REFUSED[MISSING_W1_GROUND_METRIC]")
