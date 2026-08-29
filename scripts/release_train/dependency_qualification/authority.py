from . import Refusal
from .policy import DependencyPolicy

def admit_action(policy: DependencyPolicy, action: str) -> str:
    normalized=action.upper()
    if normalized in policy.refused_actions:
        raise Refusal(f'REFUSED[CONSEQUENTIAL_ACTION]:{normalized}')
    if normalized not in {'OBSERVE','SELECT','CONSTRUCT','VERIFY'}:
        raise Refusal(f'REFUSED[UNKNOWN_ACTION]:{normalized}')
    return normalized
