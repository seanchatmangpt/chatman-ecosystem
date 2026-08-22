from enum import Enum
from .subject import Refusal
class ActionClass(str,Enum): OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'
def admit_action(action):
    if action is ActionClass.DO: raise Refusal('REFUSED_BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO')
