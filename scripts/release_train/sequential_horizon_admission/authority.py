from enum import StrEnum
from .errors import Refused
class ActionClass(StrEnum): OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def admit_action(action):
    if action is ActionClass.DO: raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
    return action
