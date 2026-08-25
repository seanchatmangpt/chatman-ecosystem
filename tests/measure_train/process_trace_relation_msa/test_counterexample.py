import unittest
from scripts.measure_train.process_trace_relation_msa.counterexample import minimal_counterexample
from scripts.measure_train.process_trace_relation_msa.subject import Refused
class T(unittest.TestCase):
 def test_minimal(self):
  c=minimal_counterexample(("a","b","c"),("a","x","c"))
  self.assertEqual(c.prefix_length,2)
  with self.assertRaises(Refused): minimal_counterexample(("a",),("a",))
