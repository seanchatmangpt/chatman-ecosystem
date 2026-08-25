from enum import Enum
from .refusal import require

class ActionClass(str,Enum):
    OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'

def admit_action(action: ActionClass, broker: str | None = None) -> ActionClass:
    if action is ActionClass.DO:
        require(broker=='BRCE','DO_REQUIRES_BRCE')
    return action
