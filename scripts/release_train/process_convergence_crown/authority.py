from enum import Enum
from .refusal import Refused

class ActionClass(str, Enum):
    OBSERVE="OBSERVE"
    SELECT="SELECT"
    CONSTRUCT="CONSTRUCT"
    VERIFY="VERIFY"
    CONSEQUENTIAL="CONSEQUENTIAL"

def require_broker(action: ActionClass, broker: str = ""):
    if action is ActionClass.CONSEQUENTIAL and broker != "BRCE":
        raise Refused("BRCE_REQUIRED")
    return action
