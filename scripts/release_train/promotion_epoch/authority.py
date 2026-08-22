ALLOWED={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
CONSEQUENTIAL={"DO","MERGE","RELEASE","DEPLOY","MESSAGE","SPEND","DELETE","CLOUD_ACTUATE"}
class AuthorityRefusal(PermissionError): pass
def admit(action):
    if action in ALLOWED: return action
    if action in CONSEQUENTIAL: raise AuthorityRefusal(f"REFUSED[BRCE_REQUIRED:{action}]")
    raise AuthorityRefusal("REFUSED[UNKNOWN_AUTHORITY_CLASS]")
