ALLOWED={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}

def admit_action(action):
    if action=="DO": raise PermissionError("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
    if action not in ALLOWED: raise PermissionError("REFUSED[UNKNOWN_AUTHORITY_CLASS]")
    return action

def qualification_plan():
    return ("VERIFY","CONSTRUCT")
