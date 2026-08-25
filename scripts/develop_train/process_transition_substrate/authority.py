from enum import Enum
from .errors import Refused
class ActionClass(str,Enum):
    OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def admit_action(action:ActionClass, broker:str|None=None, receipt_digest:str|None=None, postcondition:bool=False):
    if action is ActionClass.DO:
        if broker!="BRCE" or not receipt_digest or not postcondition:
            raise Refused("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
    return True
