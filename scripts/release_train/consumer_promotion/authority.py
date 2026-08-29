_ALLOWED={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
_CONSEQUENTIAL={"DO","MERGE","RELEASE","DEPLOY","MESSAGE","SPEND","DELETE","LIVE_CLOUD"}
def require(action:str, brce_receipt:bool=False)->str:
    if action in _ALLOWED: return "ADMITTED"
    if action in _CONSEQUENTIAL:
        if not brce_receipt: raise PermissionError("REFUSED[BRCE_REQUIRED]")
        raise PermissionError("REFUSED[OUT_OF_SCOPE_CONSEQUENTIAL_DO]")
    raise ValueError("REFUSED[UNKNOWN_ACTION]")
