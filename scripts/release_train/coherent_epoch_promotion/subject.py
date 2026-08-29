from __future__ import annotations
from dataclasses import dataclass
import re

_SUBJECT = re.compile(r'^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})$')

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    @classmethod
    def parse(cls, value: str) -> 'Subject':
        match = _SUBJECT.fullmatch(value)
        if not match:
            raise ValueError('REFUSED[INEXACT_SUBJECT]')
        return cls(match.group('repo'), match.group('sha'))

    def key(self) -> str:
        return f'{self.repo}@{self.sha}'
