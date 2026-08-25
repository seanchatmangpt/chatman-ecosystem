import unittest
from fractions import Fraction
from scripts.measure_train.replica_quorum_msa.topology import ReplicaUniverse
from scripts.measure_train.replica_quorum_msa.subject import Refused
class O:
 def __init__(self,r): self.replica_id=r
class T(unittest.TestCase):
 def test_exact_coverage(self):
  u=ReplicaUniverse.from_ids(["a","b","c"]); self.assertEqual(u.quorum_size(),2)
  self.assertEqual(u.coverage([O("a"),O("b")]),Fraction(2,3))
  with self.assertRaises(Refused): ReplicaUniverse.from_ids(["a","a"])
