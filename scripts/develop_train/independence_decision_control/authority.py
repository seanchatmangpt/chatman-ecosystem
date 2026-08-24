from enum import Enum

from .errors import Refused


class ActionClass(str, Enum):
    OBSERVE = "OBSERVE"
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    VERIFY = "VERIFY"
    DO = "DO"


def admit(action, broker=None):
    if action is ActionClass.DO and broker != "BRCE":
        raise Refused("UNRECEIPTED_ACTUATION")
    return True
