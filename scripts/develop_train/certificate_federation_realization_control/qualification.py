from dataclasses import dataclass
from .observation import admit as admit_observations
from .correlation import phi, require_independent
from .censoring import census
from .availability import wilson
from .calibration import calibrate
from .frontier import current
from .coverage import require_transport_coverage
from .methodology import require_methodologies
from .correspondence import require_engine_region_correspondence
from .dependency import blockers
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    standing: str
    availability_lower: float
    censoring_fraction: float
    false_current_rate: float
    receipt: Receipt | None

def qualify(subject, certificate, observations, paired_failures=None, graph=None, standings=None):
    obs = admit_observations(observations, certificate.generation)
    hard = blockers(graph or {}, standings or {})
    if hard:
        return Qualification("BUILD_BROKEN", 0.0, 1.0, 1.0, None)
    require_transport_coverage(obs)
    require_methodologies(obs)
    require_engine_region_correspondence(obs)
    if paired_failures:
        require_independent(phi(*paired_failures))
    availability = wilson(obs)
    censor = census(obs)
    cal = current([calibrate(obs, certificate.generation)])
    standing = "PARTIAL_ALIVE"
    if not cal.admitted or availability.lower < 0.5 or censor.fraction > 0.5:
        standing = "UNKNOWN"
    receipt = Receipt(subject.key, certificate.generation, standing, cal.digest)
    return Qualification(standing, availability.lower, censor.fraction, cal.false_current_rate, receipt)
