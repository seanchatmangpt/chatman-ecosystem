from enum import StrEnum
class ActionClass(StrEnum): OBSERVE='OBSERVE'; SELECT='SELECT'; CONSTRUCT='CONSTRUCT'; VERIFY='VERIFY'; DO='DO'
class RefusedAuthority(PermissionError):pass
def require_nonconsequential(action):
 if action is ActionClass.DO:raise RefusedAuthority('REFUSED[BRCE_REQUIRED_FOR_CONSEQUENTIAL_DO]')
