from __future__ import annotations

ALLOWED=frozenset({"OBSERVE","SELECT","CONSTRUCT","VERIFY"})
CONSEQUENTIAL=frozenset({"DO","MERGE","RELEASE","DEPLOY","MESSAGE","SPEND","DELETE","LIVE_CLOUD"})

class AuthorityRefusal(PermissionError):
    pass

def require(action: str) -> None:
    if action in ALLOWED:
        return
    if action in CONSEQUENTIAL:
        raise AuthorityRefusal("REFUSED[BRCE_REQUIRED]")
    raise AuthorityRefusal("REFUSED[UNKNOWN_AUTHORITY_CLASS]")
