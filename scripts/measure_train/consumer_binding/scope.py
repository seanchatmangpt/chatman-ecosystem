from .subject import Refused
ORDER = {"FOCUSED":0,"ARTIFACT":1,"RUNTIME":1,"RECEIPT":1,"DEPENDENCY":2,"REPOSITORY":3}

def scope_satisfies(observed_scope, required_scope):
    if observed_scope not in ORDER or required_scope not in ORDER:
        raise Refused("REFUSED[UNKNOWN_SCOPE]")
    return ORDER[observed_scope] >= ORDER[required_scope]
