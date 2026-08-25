from dataclasses import dataclass
import re
from .refusal import Refused
_SUBJECT=re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$')
_HEX64=re.compile(r'^[0-9a-f]{64}$')
@dataclass(frozen=True, order=True)
class Subject:
    value:str
    def __post_init__(self):
        if not _SUBJECT.match(self.value): raise Refused('INEXACT_SUBJECT')
@dataclass(frozen=True, order=True)
class PolicyIdentity:
    generation:int
    digest:str
    def __post_init__(self):
        if self.generation < 0: raise Refused('INVALID_GENERATION')
        if not _HEX64.match(self.digest): raise Refused('INVALID_POLICY_DIGEST')
