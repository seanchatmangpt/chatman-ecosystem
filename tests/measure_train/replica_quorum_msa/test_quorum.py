import unittest
from datetime import datetime,timezone
from scripts.measure_train.replica_quorum_msa.subject import Subject,Refused
from scripts.measure_train.replica_quorum_msa.vector_clock import VectorClock
from scripts.measure_train.replica_quorum_msa.observation import ReplicaObservation
from scripts.measure_train.replica_quorum_msa.topology import ReplicaUniverse
from scripts.measure_train.replica_quorum_msa.quorum import classify_quorum
class T(unittest.TestCase):
 def test_majority_and_duplicate_fence(self):
  s=Subject("o/r","a"*40); n=datetime.now(timezone.utc); u=ReplicaUniverse.from_ids(["a","b","c"])
  def o(r): return ReplicaObservation(s,r,2,"1"*64,VectorClock.from_dict({r:1}),n,r[0]*64)
  self.assertEqual(classify_quorum(u,[o("a"),o("b")])["state"],"CURRENT_CANDIDATE")
  with self.assertRaises(Refused): classify_quorum(u,[o("a"),o("a")])
