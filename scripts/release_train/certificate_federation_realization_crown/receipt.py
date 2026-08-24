from dataclasses import dataclass
from hashlib import sha256
import json
from .subject import Subject

@dataclass(frozen=True)
class Receipt:
    schema: str
    subject: str
    generation: int
    standing: str
    calibration_digest: str
    authority: str
    actuation_performed: bool
    digest: str

def manufacture(subject: Subject, generation: int, standing: str, calibration_digest: str) -> Receipt:
    body={"schema":"chatman.certificate-federation-realization-crown/1","subject":subject.identity,
          "generation":generation,"standing":standing,"calibration_digest":calibration_digest,
          "authority":"SELECT","actuation_performed":False}
    digest=sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Receipt(**body,digest=digest)
