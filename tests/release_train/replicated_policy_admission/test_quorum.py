import unittest
from fixtures import state,POL,FRONT
from scripts.release_train.replicated_policy_admission.quorum import qualify_quorum,strict_majority
class TestQuorum(unittest.TestCase):
    def test_majority(self):
        q=qualify_quorum([state('a',clock={'a':1}),state('b',clock={'a':1,'b':1}),state('c',pol='c'*64,clock={'c':1})]); self.assertEqual((q.policy_digest,q.frontier_digest),(POL,FRONT)); self.assertEqual(len(q.agreeing),2)
    def test_minority_not_quorum(self):
        q=qualify_quorum([state('a'),state('b',pol='c'*64),state('c',pol='d'*64)]); self.assertIsNone(q.policy_digest); self.assertEqual(strict_majority(3),2)
