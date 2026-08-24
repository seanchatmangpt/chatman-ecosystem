from .refusal import refuse
def admit_action(action_class,broker=None):
    if action_class=="DO":
        if broker!="BRCE":
            refuse("DO_REQUIRES_BRCE")
        return "BRCE"
    if action_class not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}:
        refuse("UNKNOWN_ACTION_CLASS")
    return action_class
