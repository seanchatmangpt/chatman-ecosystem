import re
from dataclasses import dataclass
from .errors import Refused
_HEX64=re.compile(r"^[0-9a-f]{64}$")
@dataclass(frozen=True)
class ControllerIdentity:
    generation:int; digest:str; calibration_generation:int; calibration_digest:str
    def __post_init__(self):
        if self.generation<0 or self.calibration_generation<0: raise Refused("INVALID_GENERATION")
        if not _HEX64.fullmatch(self.digest) or not _HEX64.fullmatch(self.calibration_digest): raise Refused("INVALID_DIGEST")
