from enum import Enum
from .errors import Refused
class ActionClass(str,Enum):
    OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'
def admit(action,broker=None):
    if action==ActionClass.DO and broker!='BRCE': raise Refused('REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]')
    return True
