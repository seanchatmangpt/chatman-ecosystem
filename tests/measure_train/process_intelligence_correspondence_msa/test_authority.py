import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.authority import admit_authority,measurement_authority
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Refused
class T(unittest.TestCase):
 def test_brce_path_and_measurement(self):
  self.assertFalse(measurement_authority()["actuation_performed"])
  with self.assertRaises(Refused): admit_authority(("SEMANTIC_ADMISSION","DO"),True)
