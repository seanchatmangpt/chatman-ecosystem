import unittest
from fractions import Fraction
from datetime import datetime,timezone
from scripts.measure_train.evidence_voi.candidate import MeasurementCandidate
from scripts.measure_train.evidence_voi.calibration import SensorCalibration
from scripts.measure_train.evidence_voi.frontier import frontier_digest,admit_frontier
from scripts.measure_train.evidence_voi.subject import Refused
class T(unittest.TestCase):
 def test_generation_movement_invalidates(self):
  now=datetime.now(timezone.utc); c=MeasurementCandidate("a","f","d","REPOSITORY",Fraction(1),1)
  old=SensorCalibration("a",1,10,Fraction(9,10),Fraction(1,10),now); digest=frontier_digest([c],[old])
  new=SensorCalibration("a",2,10,Fraction(8,10),Fraction(2,10),now)
  with self.assertRaises(Refused): admit_frontier(digest,[c],[new])
