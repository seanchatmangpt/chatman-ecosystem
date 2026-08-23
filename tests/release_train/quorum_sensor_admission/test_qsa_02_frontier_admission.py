import unittest
from dataclasses import replace
from scripts.release_train.quorum_sensor_admission import AdmissionPolicy, CalibrationFrontier, Refused, admit_sensor
from common import SUBJECT, model, frontier, visibility
class FrontierAdmissionCourt(unittest.TestCase):
 def test_current_model_admits(self):
  m=model(); admit_sensor(m,frontier(m),visibility(),AdmissionPolicy())
 def test_stale_and_divergent_refuse(self):
  current=model(); stale=replace(current,generation=6)
  with self.assertRaises(Refused): frontier(current).admits(stale)
  with self.assertRaises(Refused): CalibrationFrontier.from_models(SUBJECT,[current,replace(current,detector_family="other")])
if __name__=="__main__": unittest.main()
