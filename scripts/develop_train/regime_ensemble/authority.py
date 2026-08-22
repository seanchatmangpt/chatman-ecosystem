from __future__ import annotations
from enum import Enum

class ActionClass(str, Enum):
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    DO = "DO"

def admit_action(action: ActionClass) -> None:
    if action is ActionClass.DO:
        raise PermissionError("REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]")
