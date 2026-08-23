from dataclasses import dataclass
import re
from .refusal import Refused

_SHA = re.compile(r"^[0-9a-f]{40}$")
_DIGEST = re.compile(r"^[0-9a-f]{64}$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    def __post_init__(self):
        if self.repo.count("/") != 1 or not _SHA.fullmatch(self.sha):
            raise Refused("INEXACT_SUBJECT")

@dataclass(frozen=True, order=True)
class PolicyIdentity:
    generation: int
    digest: str
    def __post_init__(self):
        if self.generation < 0 or not _DIGEST.fullmatch(self.digest):
            raise Refused("INVALID_POLICY_IDENTITY")
