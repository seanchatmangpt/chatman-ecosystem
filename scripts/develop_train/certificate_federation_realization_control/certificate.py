from dataclasses import dataclass
import re
from .errors import Refused

_HEX = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True)
class Certificate:
    generation: int
    semantic_digest: str
    certificate_digest: str

    def __post_init__(self):
        if self.generation < 0:
            raise Refused("INVALID_CERTIFICATE_GENERATION")
        if not _HEX.fullmatch(self.semantic_digest) or not _HEX.fullmatch(self.certificate_digest):
            raise Refused("INVALID_CERTIFICATE_DIGEST")
