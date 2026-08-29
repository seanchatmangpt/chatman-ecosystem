from enum import Enum
from .subject import Refused
class ActionClass(str,Enum): OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def require_action(action):
    a=ActionClass(action)
    if a is ActionClass.DO: raise Refused("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
    return a
