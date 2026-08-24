from enum import Enum
from .errors import Refused

class Action(str, Enum):
    OBSERVE = "OBSERVE"
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    VERIFY = "VERIFY"
    DO = "DO"

def admit(action, broker=None):
    action = Action(action)
    if action == Action.DO and broker != "BRCE":
        raise Refused("BRCE_REQUIRED_FOR_DO")
    return action
