from dataclasses import dataclass
from fractions import Fraction
import hashlib
from .oracle import differential
from .consequence import evaluate

@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    mean_oracle_gap: Fraction
    max_oracle_gap: Fraction
    consequence_mae: Fraction
    false_safe_rate: Fraction

    def admitted(self, max_oracle_gap=Fraction(1,100), max_mae=Fraction(1,10), max_false_safe=Fraction(1,20)) -> bool:
        return self.support >= 11 and self.max_oracle_gap <= max_oracle_gap and self.consequence_mae <= max_mae and self.false_safe_rate <= max_false_safe


def calibrate(certificate, observations) -> Calibration:
    oracle = differential(certificate, observations)
    consequence = evaluate(observations)
    payload = f"{certificate.certificate_digest}:{certificate.generation}:{oracle.support}:{oracle.mean_absolute_gap}:{oracle.max_absolute_gap}:{consequence.mean_absolute_error}:{consequence.false_safe_rate}"
    digest = hashlib.sha256(payload.encode()).hexdigest()
    return Calibration(certificate.generation,digest,oracle.support,oracle.mean_absolute_gap,oracle.max_absolute_gap,consequence.mean_absolute_error,consequence.false_safe_rate)
