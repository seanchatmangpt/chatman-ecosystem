from dataclasses import dataclass
import re
from .refusal import Refused
_SHA=re.compile(r"^[0-9a-f]{40}$"); _REPO=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
@dataclass(frozen=True)
class Subject:
    repo:str; sha:str; semantic:str; generation:int
    def __post_init__(self):
        if not _REPO.fullmatch(self.repo) or not _SHA.fullmatch(self.sha) or not self.semantic or self.generation < 0:
            raise Refused("INVALID_SUBJECT")
