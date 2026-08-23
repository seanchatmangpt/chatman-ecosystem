import unittest
from scripts.develop_train.replicated_evidence_state.mutation import Mutation
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock
from scripts.develop_train.replicated_evidence_state.errors import Refused

class MutationTest(unittest.TestCase):
    def test_generation_must_advance_exactly_one(self):
        Mutation("r","o/r@"+"a"*40,1,2,"b"*64,VectorClock.from_dict({"r":2}))
        with self.assertRaises(Refused): Mutation("r","o/r@"+"a"*40,1,3,"b"*64,VectorClock.from_dict({"r":3}))
