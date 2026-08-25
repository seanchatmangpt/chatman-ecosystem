import unittest
from scripts.measure_train.delta.ci_vector import CIVector
class T(unittest.TestCase):
 def test_transition_preserves_unknown(self):
  a=CIVector.from_mapping({"x":"PASS"}); b=CIVector.from_mapping({"x":"FAIL","y":"PENDING"})
  self.assertEqual(a.transition(b),(('x','PASS','FAIL'),('y','UNKNOWN','PENDING')))
