from enum import Enum
from .errors import Refused
class Action(str,Enum): OBSERVE="OBSERVE"; SELECT="SELECT"; CONSTRUCT="CONSTRUCT"; VERIFY="VERIFY"; DO="DO"
def admit(action,broker=None):
    if action==Action.DO and broker!="BRCE": raise Refused("DO_REQUIRES_BRCE")
    return action
