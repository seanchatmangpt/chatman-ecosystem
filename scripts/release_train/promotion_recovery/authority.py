from enum import Enum
from .subject import Refusal
class ActionClass(str,Enum):
    OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'
def require(action):
    if action is ActionClass.DO: raise Refusal('REFUSED[BRCE_REQUIRED]')
    return action
