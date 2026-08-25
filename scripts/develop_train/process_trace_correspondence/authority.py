from enum import Enum
from .errors import Refused
class ActionClass(str,Enum): SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def admit(action):
    a=ActionClass(action)
    if a is ActionClass.DO: raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
    return a
