import re
from dataclasses import dataclass
from .errors import Refused
PAT=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
@dataclass(frozen=True, order=True)
class Subject:
    value:str
    def __post_init__(self):
        if not PAT.fullmatch(self.value): raise Refused("INEXACT_SUBJECT")
