import unittest
from scripts.develop_train.replicated_evidence_state.quorum import qualified
from scripts.develop_train.replicated_evidence_state.replica_state import ReplicaState
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock

def s(replica,value): return ReplicaState(replica,"o/r@"+"a"*40,1,value*64,VectorClock.from_dict({replica:1}))
class QuorumTest(unittest.TestCase):
    def test_majority_required(self):
        self.assertEqual(qualified([s("a","b"),s("b","b"),s("c","c")]),(True,"b"*64))
        self.assertEqual(qualified([s("a","a"),s("b","b"),s("c","c")]),(False,None))
