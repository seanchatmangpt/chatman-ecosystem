from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class Calibration:
    generation:int; support:int; mae:Fraction; false_safe_rate:Fraction; digest:str
def calibrate(certificate, observations):
    from .consequence import evaluate
    c=evaluate(observations)
    if len(observations) < 4: raise Refused("INSUFFICIENT_CALIBRATION_SUPPORT")
    digest=f"{certificate.digest}:{certificate.generation}:{len(observations)}:{c.mae}:{c.false_safe_rate}"
    return Calibration(certificate.generation,len(observations),c.mae,c.false_safe_rate,digest)
