from enum import Enum
from .refusals import Refused
class ActionClass(str,Enum):
    SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; DO="DO"
def admit_action(action:ActionClass)->None:
    if action is ActionClass.DO: raise Refused("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
