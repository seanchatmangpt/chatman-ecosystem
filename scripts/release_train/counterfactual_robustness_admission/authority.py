from enum import Enum
from .refusal import refuse
class ActionClass(str,Enum): OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'
def admit_action(action):
    if action is ActionClass.DO: refuse("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO")
    return action
