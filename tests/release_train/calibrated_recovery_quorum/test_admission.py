import unittest
from datetime import datetime,timezone
from scripts.release_train.calibrated_recovery_quorum.source import EvidenceSource
from scripts.release_train.calibrated_recovery_quorum.witness import RecoveryWitness
from scripts.release_train.calibrated_recovery_quorum.calibration import CalibrationModel
from scripts.release_train.calibrated_recovery_quorum.admission import admit_witness
class T(unittest.TestCase):
 def test_under_support(self):
  s=EvidenceSource("p","r","a","f"); w=RecoveryWitness("x",s.fingerprint,"PASS",datetime.now(timezone.utc)); m=CalibrationModel(s.fingerprint,2,2,0,0,0)
  self.assertFalse(admit_witness(w,s,m,datetime.now(timezone.utc),6)["admitted"])
