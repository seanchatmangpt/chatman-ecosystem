from __future__ import annotations
_ALLOWED={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
_CONSEQUENTIAL={"DO","MERGE","RELEASE","DEPLOY","MESSAGE","SPEND","DELETE","CLOUD_ACTUATE"}

class AuthorityRefusal(PermissionError):
    pass

def admit_action(action: str) -> str:
    normalized=action.upper()
    if normalized in _ALLOWED:
        return normalized
    if normalized in _CONSEQUENTIAL:
        raise AuthorityRefusal("REFUSED[BRCE_REQUIRED_FOR_DO]")
    raise AuthorityRefusal("REFUSED[UNKNOWN_AUTHORITY_ACTION]")
