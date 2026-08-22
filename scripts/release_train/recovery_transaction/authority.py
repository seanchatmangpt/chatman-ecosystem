from enum import Enum
from .subject import Refusal
class ActionClass(str,Enum): OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def require(action:ActionClass)->None:
    if action is ActionClass.DO: raise Refusal("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
