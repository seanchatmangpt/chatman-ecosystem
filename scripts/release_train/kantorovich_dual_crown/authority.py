from .refusal import Refused
ALLOWED={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
def admit(action,broker=None):
    if action=="DO":
        if broker!="BRCE": raise Refused("DO_REQUIRES_BRCE")
        return "DO"
    if action not in ALLOWED: raise Refused("UNKNOWN_AUTHORITY")
    return action
