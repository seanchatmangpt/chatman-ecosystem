import re
from dataclasses import dataclass
from .errors import Refused

_HEX40 = re.compile(r"^[0-9a-f]{40}$")

@dataclass(frozen=True, order=True)
class Subject:
    repo: str
    sha: str
    semantic_digest: str

    @classmethod
    def parse(cls, repo: str, sha: str, semantic_digest: str):
        if repo.count("/") != 1 or not all(repo.split("/")):
            raise Refused("INVALID_REPOSITORY", repo)
        if not _HEX40.fullmatch(sha):
            raise Refused("INVALID_SUBJECT_SHA", sha)
        if not re.fullmatch(r"[0-9a-f]{64}", semantic_digest):
            raise Refused("INVALID_SEMANTIC_DIGEST", semantic_digest)
        return cls(repo, sha, semantic_digest)

    @property
    def key(self):
        return f"{self.repo}@{self.sha}#{self.semantic_digest}"
