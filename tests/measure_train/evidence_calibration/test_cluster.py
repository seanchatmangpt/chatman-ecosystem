import unittest
from scripts.measure_train.evidence_calibration.cluster import EvidenceCluster,validate_disjoint
from scripts.measure_train.evidence_calibration.subject import Refused
class T(unittest.TestCase):
 def test_overlap_refuses(self):
  with self.assertRaises(Refused):
   validate_disjoint([EvidenceCluster("a",("x",)),EvidenceCluster("b",("x",))])
