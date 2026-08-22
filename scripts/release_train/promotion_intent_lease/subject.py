from dataclasses import dataclass
import re

SUBJECT_RE = re.compile(r'^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40})$')

class Refusal(ValueError):
    pass

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str

    @classmethod
    def parse(cls, value: str) -> 'Subject':
        m = SUBJECT_RE.fullmatch(value)
        if not m:
            raise Refusal('REFUSED[INEXACT_SUBJECT]')
        return cls(m.group('repo'), m.group('sha'))

    def __str__(self) -> str:
        return f'{self.repo}@{self.sha}'
