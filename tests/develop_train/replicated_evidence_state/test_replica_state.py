import unittest
from scripts.develop_train.replicated_evidence_state.replica_state import ReplicaState
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock

class ReplicaStateTest(unittest.TestCase):
    def test_digest_is_deterministic(self):
        s=ReplicaState("r1","o/r@"+"a"*40,1,"b"*64,VectorClock.from_dict({"r1":1}))
        self.assertEqual(s.digest(),s.digest())
        self.assertEqual(len(s.digest()),64)
