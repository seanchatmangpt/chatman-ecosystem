from enum import Enum
from .refusal import Refused
class ActionClass(str,Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def admit(action, broker=None):
    a=ActionClass(action)
    if a is ActionClass.DO and broker!="BRCE": raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
    return True
