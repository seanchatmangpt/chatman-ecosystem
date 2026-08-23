import unittest
from fractions import Fraction
from scripts.measure_train.replica_quorum_msa.topology import ReplicaUniverse
from scripts.measure_train.replica_quorum_msa.observability import observability
class O:
 def __init__(self,r): self.replica_id=r
class T(unittest.TestCase):
 def test_permutation_invariant(self):
  u=ReplicaUniverse.from_ids(["a","b","c","d"])
  a=observability(u,[O("a"),O("b")]); b=observability(u,[O("b"),O("a")])
  self.assertEqual(a,b); self.assertEqual(a["coverage"],Fraction(1,2)); self.assertFalse(a["quorum_covered"])
