from dataclasses import dataclass
from . import Refusal

@dataclass(frozen=True)
class AdvisoryFinding:
    advisory_id: str
    crate: str
    status: str


def admit_advisories(findings: list[AdvisoryFinding]) -> tuple[AdvisoryFinding, ...]:
    live = tuple(sorted((f for f in findings if f.status in {'vulnerable','unmaintained','unsound'}), key=lambda f:(f.advisory_id,f.crate)))
    if live:
        raise Refusal('REFUSED[ACTIVE_RUSTSEC_ADVISORY]:' + ','.join(f.advisory_id for f in live))
    return tuple(sorted(findings, key=lambda f:(f.advisory_id,f.crate)))
