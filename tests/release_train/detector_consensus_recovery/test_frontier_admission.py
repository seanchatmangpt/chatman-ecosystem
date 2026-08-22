import unittest
from dataclasses import replace
from scripts.release_train.detector_consensus_recovery.frontier import unique_current
from scripts.release_train.detector_consensus_recovery.admission import admit_votes
from helpers import detector,generation,vote
class Court(unittest.TestCase):
 def test_unique_current(self):
  d=detector("c","CUSUM","r1"); g=generation(d); self.assertEqual(unique_current([g])[d.fingerprint].generation,1)
 def test_stale_generation_refuses(self):
  d=detector("c","CUSUM","r1"); g=generation(d,2); v=replace(vote(d,g,"STABLE"),calibration_generation=1)
  with self.assertRaisesRegex(ValueError,"STALE_CALIBRATION_GENERATION"): admit_votes([v],[g])
