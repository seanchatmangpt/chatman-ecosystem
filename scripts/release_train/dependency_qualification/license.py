from . import Refusal
from .policy import DependencyPolicy

def admit_licenses(policy: DependencyPolicy, licenses: dict[str,str]) -> tuple[tuple[str,str], ...]:
    if not licenses:
        raise Refusal('REFUSED[MISSING_LICENSE_EVIDENCE]')
    out=[]
    for crate, license_id in sorted(licenses.items()):
        policy.admit_license(license_id)
        out.append((crate, license_id))
    return tuple(out)
