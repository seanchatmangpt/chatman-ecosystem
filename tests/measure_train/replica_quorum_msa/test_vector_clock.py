import unittest
from scripts.measure_train.replica_quorum_msa.vector_clock import VectorClock
class T(unittest.TestCase):
 def test_partial_order_join(self):
  a=VectorClock.from_dict({"a":1}); b=VectorClock.from_dict({"a":2,"b":1}); c=VectorClock.from_dict({"c":1})
  self.assertEqual(a.compare(b),"BEFORE"); self.assertEqual(b.compare(c),"CONCURRENT")
  self.assertEqual(a.join(c).as_dict(),{"a":1,"c":1})
