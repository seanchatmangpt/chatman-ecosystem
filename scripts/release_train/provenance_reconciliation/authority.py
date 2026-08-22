from __future__ import annotations

from dataclasses import dataclass

from .model import Refused

NON_CONSEQUENTIAL = frozenset({"OBSERVE", "SELECT", "CONSTRUCT", "VERIFY"})
CONSEQUENTIAL = frozenset({"DO", "MERGE", "RELEASE", "DEPLOY", "MESSAGE", "SPEND", "DELETE", "LIVE_CLOUD"})


@dataclass(frozen=True)
class AuthorityContext:
    owner: str
    brce_receipt: str | None = None

    def admit(self, action: str) -> None:
        if action in NON_CONSEQUENTIAL:
            return
        if action in CONSEQUENTIAL:
            if not self.brce_receipt:
                raise Refused("BRCE_REQUIRED", action)
            return
        raise Refused("UNKNOWN_AUTHORITY_ACTION", action)
