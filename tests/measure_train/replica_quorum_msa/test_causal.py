import unittest
from datetime import datetime,timezone
from scripts.measure_train.replica_quorum_msa.subject import Subject
from scripts.measure_train.replica_quorum_msa.vector_clock import VectorClock
from scripts.measure_train.replica_quorum_msa.observation import ReplicaObservation
from scripts.measure_train.replica_quorum_msa.causal import causal_profile,maximal_observations
class T(unittest.TestCase):
 def test_concurrency_visible(self):
  s=Subject("o/r","a"*40); n=datetime.now(timezone.utc)
  a=ReplicaObservation(s,"a",1,"1"*64,VectorClock.from_dict({"a":1}),n,"a"*64)
  b=ReplicaObservation(s,"b",1,"2"*64,VectorClock.from_dict({"b":1}),n,"b"*64)
  self.assertEqual(causal_profile([a,b])["CONCURRENT"],1); self.assertEqual(len(maximal_observations([a,b])),2)
