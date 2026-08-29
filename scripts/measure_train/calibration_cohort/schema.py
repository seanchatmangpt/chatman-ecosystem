import hashlib
from dataclasses import dataclass
from .subject import Refused
@dataclass(frozen=True, order=True)
class CalibrationSchema:
    truth_ontology:str; detector_policy:str; feature_contract:str
    def __post_init__(self):
        if not all(x.strip() for x in (self.truth_ontology,self.detector_policy,self.feature_contract)):
            raise Refused("REFUSED[EMPTY_CALIBRATION_SCHEMA]")
    @property
    def fingerprint(self):
        return hashlib.sha256("\0".join((self.truth_ontology,self.detector_policy,self.feature_contract)).encode()).hexdigest()
