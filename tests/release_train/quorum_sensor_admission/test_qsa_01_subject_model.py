import unittest
from fractions import Fraction
from scripts.release_train.quorum_sensor_admission import Refused, Subject, SensorCalibration
from common import SUBJECT, model
class SubjectModelCourt(unittest.TestCase):
 def test_exact_subject_and_digest_are_deterministic(self): self.assertEqual(model().digest(),model().digest()); self.assertEqual(len(SUBJECT.sha),40)
 def test_short_sha_and_invalid_rate_refuse(self):
  with self.assertRaises(Refused): Subject.parse("seanchatmangpt/chatman-ecosystem@deadbeef")
  with self.assertRaises(Refused): SensorCalibration(SUBJECT,1,10,Fraction(2),Fraction(0),Fraction(0),Fraction(1),"x")
if __name__=="__main__": unittest.main()
