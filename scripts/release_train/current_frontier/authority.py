from __future__ import annotations

class Refusal(PermissionError):
    pass

SAFE={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
CONSEQUENTIAL={"DO","MERGE","RELEASE","DEPLOY","MESSAGE","SPEND","DELETE","LIVE_CLOUD"}

def require(action: str, brce_receipt: bool=False) -> None:
    if action in SAFE:
        return
    if action in CONSEQUENTIAL and brce_receipt:
        return
    if action in CONSEQUENTIAL:
        raise Refusal(f"REFUSED[BRCE_REQUIRED]:{action}")
    raise Refusal(f"REFUSED[UNKNOWN_ACTION]:{action}")
