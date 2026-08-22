ALLOWED={"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
def require_action(action):
    if action not in ALLOWED:
        raise PermissionError("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
    return action
