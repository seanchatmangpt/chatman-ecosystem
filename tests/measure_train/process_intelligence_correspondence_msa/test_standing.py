import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.standing import standing
class T(unittest.TestCase):
 def test_failure_dominates(self):
  c={"rail_failures":1,"rail_unknown":0,"methodology_complete":True,"oracle_state":"AGREE","region_state":"CURRENT","authority_state":"UNOBSERVED"}
  self.assertEqual(standing(c),"BUILD_BROKEN")
