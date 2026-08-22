from __future__ import annotations
from enum import Enum
from .subject import Refusal

class ActionClass(str, Enum):
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    VERIFY = "VERIFY"
    DO = "DO"

def require(action: ActionClass) -> None:
    if action is ActionClass.DO:
        raise Refusal("BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO", "DEVELOP train has no DO authority")
