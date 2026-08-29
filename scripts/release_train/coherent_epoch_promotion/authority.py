from __future__ import annotations
_ALLOWED={'OBSERVE','SELECT','CONSTRUCT','VERIFY'}
_CONSEQUENTIAL={'DO','MERGE','RELEASE','DEPLOY','MESSAGE','SPEND','DELETE','LIVE_CLOUD'}

def require(action: str) -> None:
    if action in _ALLOWED: return
    if action in _CONSEQUENTIAL: raise PermissionError('REFUSED[BRCE_REQUIRED]')
    raise PermissionError('REFUSED[UNKNOWN_ACTION_CLASS]')
