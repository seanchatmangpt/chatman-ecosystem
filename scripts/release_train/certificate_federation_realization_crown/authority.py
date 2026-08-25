from dataclasses import dataclass
from .refusal import Refused

@dataclass(frozen=True)
class Action:
    authority: str
    broker: str | None = None

def admit_action(action: Action) -> Action:
    if action.authority == "DO" and action.broker != "BRCE":
        raise Refused("DO_REQUIRES_BRCE")
    if action.authority not in {"OBSERVE","SELECT","CONSTRUCT","VERIFY","DO"}:
        raise Refused("UNKNOWN_AUTHORITY")
    return action
