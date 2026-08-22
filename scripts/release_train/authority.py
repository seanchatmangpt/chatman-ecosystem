from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable

class AuthorityRefusal(ValueError):
    pass

_ALLOWED = {"OBSERVE", "SELECT", "CONSTRUCT", "VERIFY"}
_FORBIDDEN = {"DO", "MERGE", "RELEASE", "DEPLOY", "MESSAGE", "SPEND", "DELETE", "CLOUD_ACTUATE"}

@dataclass(frozen=True)
class ProposedAction:
    kind: str
    target: str

def admit_actions(actions: Iterable[ProposedAction]) -> tuple[ProposedAction, ...]:
    admitted=[]
    for action in actions:
        if action.kind in _FORBIDDEN:
            raise AuthorityRefusal(f"REFUSED[CONSEQUENTIAL_ACTION:{action.kind}]")
        if action.kind not in _ALLOWED:
            raise AuthorityRefusal(f"REFUSED[UNKNOWN_AUTHORITY_CLASS:{action.kind}]")
        admitted.append(action)
    return tuple(admitted)
