import re
from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True, order=True)
class ComponentRef:
    component_id: str
    repo: str
    ref: str
    expected_sha: str
    required: bool = True

    def __post_init__(self):
        if not self.component_id.strip():
            raise Refused("REFUSED[EMPTY_COMPONENT_ID]")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repo):
            raise Refused("REFUSED[INVALID_COMPONENT_REPOSITORY]")
        if not self.ref.strip():
            raise Refused("REFUSED[EMPTY_COMPONENT_REF]")
        if not re.fullmatch(r"[0-9a-f]{40}", self.expected_sha):
            raise Refused("REFUSED[INEXACT_COMPONENT_SHA]")
