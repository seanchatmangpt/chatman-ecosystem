import unittest
from scripts.develop_train.replicated_evidence_state.conflict import classify
from scripts.develop_train.replicated_evidence_state.replica_state import ReplicaState
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock

def s(replica,value): return ReplicaState(replica,"o/r@"+"a"*40,2,value*64,VectorClock.from_dict({replica:2}))
class ConflictTest(unittest.TestCase):
    def test_split_brain_is_not_flattened(self):
        self.assertEqual(classify([s("a","b"),s("b","c")]),"SPLIT_BRAIN")
        self.assertEqual(classify([s("a","b"),s("b","b")]),"CONSISTENT")
