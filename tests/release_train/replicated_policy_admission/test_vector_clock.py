import unittest
from scripts.release_train.replicated_policy_admission.vector_clock import VectorClock,Relation
class TestClock(unittest.TestCase):
    def test_partial_order_and_join(self):
        a=VectorClock.from_dict({'a':1,'b':0}); b=VectorClock.from_dict({'a':1,'b':2})
        self.assertEqual(a.compare(b),Relation.BEFORE); self.assertEqual(a.join(b),b)
    def test_concurrent(self): self.assertEqual(VectorClock.from_dict({'a':1}).compare(VectorClock.from_dict({'b':1})),Relation.CONCURRENT)
