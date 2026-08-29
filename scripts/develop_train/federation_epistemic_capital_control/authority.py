from enum import Enum
from .errors import Refused
class Action(str,Enum): OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'
def admit(a,broker=None):
    if a==Action.DO and broker!='BRCE': raise Refused('BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO')
    return a
