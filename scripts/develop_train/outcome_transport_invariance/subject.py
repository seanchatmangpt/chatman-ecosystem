import re
from dataclasses import dataclass
from .errors import Refused
R = re.compile(r"^([\w.-]+/[\w.-]+)@([0-9a-f]{40})#([0-9a-f]{64})$")

@dataclass(frozen=True)
class Subject:
    repo: str
    sha: str
    semantic: str

    @classmethod
    def parse(cls, value):
        match = R.fullmatch(value)
        if not match:
            raise Refused("INEXACT_SUBJECT", value)
        return cls(*match.groups())

    @property
    def key(self):
        return f"{self.repo}@{self.sha}#{self.semantic}"
