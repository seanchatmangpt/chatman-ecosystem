from enum import Enum
from .errors import Refused

class ActionClass(str,Enum):
    OBSERVE="OBSERVE"
    SELECT="SELECT"
    CONSTRUCT="CONSTRUCT"
    VERIFY="VERIFY"
    DO="DO"

def admit_action(action):
    if action==ActionClass.DO: raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
    if action not in {ActionClass.OBSERVE,ActionClass.SELECT,ActionClass.CONSTRUCT,ActionClass.VERIFY}:
        raise Refused("INVALID_ACTION_CLASS")
    return action
