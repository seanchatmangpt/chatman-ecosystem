from dataclasses import dataclass
import re
from .errors import Refused
_PAT=re.compile(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$')
@dataclass(frozen=True)
class Subject:
    key:str
    @classmethod
    def parse(cls,s):
        if not _PAT.match(s): raise Refused('REFUSED[INVALID_SUBJECT]')
        return cls(s)
