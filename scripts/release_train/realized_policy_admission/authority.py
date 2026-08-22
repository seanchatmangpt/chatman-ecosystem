from enum import Enum

class ActionClass(str, Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"

def admit_action(action: ActionClass):
    if action is ActionClass.DO:
        raise PermissionError("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
    return action
