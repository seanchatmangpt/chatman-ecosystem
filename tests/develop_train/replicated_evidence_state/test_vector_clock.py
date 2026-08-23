import unittest
from scripts.develop_train.replicated_evidence_state.vector_clock import VectorClock

class VectorClockTest(unittest.TestCase):
    def test_partial_order_join_and_concurrency(self):
        a=VectorClock.from_dict({"a":1,"b":0}); b=VectorClock.from_dict({"a":1,"b":1}); c=VectorClock.from_dict({"a":2,"b":0})
        self.assertEqual(a.compare(b),"BEFORE")
        self.assertEqual(b.compare(c),"CONCURRENT")
        self.assertEqual(VectorClock.join(b,c).as_dict(),{"a":2,"b":1})
