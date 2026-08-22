from .subject import Refusal
ALLOWED={'OBSERVE','SELECT','CONSTRUCT','VERIFY'}
def require_authority(action, brce_receipted=False):
    if action in ALLOWED:
        return action
    if action in {'DO','MERGE','RELEASE','DEPLOY','MESSAGE','SPEND','DELETE','LIVE_CLOUD'}:
        raise Refusal('REFUSED[BRCE_REQUIRED]')
    raise Refusal('REFUSED[UNKNOWN_ACTION]')
