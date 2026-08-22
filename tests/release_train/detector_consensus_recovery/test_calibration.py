import unittest
from scripts.release_train.detector_consensus_recovery.calibration import calibrate
from scripts.release_train.detector_consensus_recovery.observation import DetectorObservation
from helpers import S,NOW,detector,generation
class Court(unittest.TestCase):
 def test_good_detector_calibrates(self): self.assertEqual(generation(detector("c","CUSUM","r1")).calibration.state,"CALIBRATED")
 def test_sparse_is_insufficient(self):
  d=detector("e","EWMA","r2"); o=[DetectorObservation(S,d,"x",NOW,False,False,None)]; self.assertEqual(calibrate(o).state,"INSUFFICIENT")
 def test_unreliable_is_typed(self): self.assertEqual(generation(detector("p","PAGE_HINKLEY","r3"),bad=True).calibration.state,"UNRELIABLE")
