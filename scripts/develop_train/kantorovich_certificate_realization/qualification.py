from dataclasses import dataclass
from fractions import Fraction
from .admission import admit
from .feasibility import measure
from .independence import witness
from .calibration import calibrate
from .methodologies import require_complete as require_methods
from .strata import worst_stratum
from .receipt import Receipt

_HARD = {"BUILD_BROKEN", "BLOCKED"}

@dataclass(frozen=True)
class Qualification:
    standing: str
    calibration_digest: str | None
    worst_false_safe_rate: Fraction | None
    receipt: Receipt | None


def qualify(subject, certificate, observations, dependencies=()):
    hard = next((item for item in dependencies if item in _HARD), None)
    if hard:
        return Qualification(hard, None, None, None)
    obs = admit(certificate, observations)
    if not measure(certificate).exact:
        return Qualification("UNSUPPORTED", None, None, None)
    witness(obs)
    require_methods(obs)
    calibration = calibrate(certificate, obs)
    worst = worst_stratum(obs)
    worst_rate = worst[0] if worst else Fraction(0, 1)
    standing = "PARTIAL_ALIVE" if calibration.admitted() and worst_rate <= Fraction(1, 20) else "UNKNOWN"
    receipt = Receipt(subject.key, certificate.certificate_digest, calibration.digest, standing)
    return Qualification(standing, calibration.digest, worst_rate, receipt)
