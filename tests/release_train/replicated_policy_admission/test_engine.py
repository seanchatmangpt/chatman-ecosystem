import unittest
from fixtures import state,subject,lease,expected,deps,NOW
from scripts.release_train.replicated_policy_admission.engine import qualify
class TestEngine(unittest.TestCase):
    def test_sequential_majority_qualifies_boundedly(self):
        states=[state('a',clock={'a':1}),state('b',clock={'a':1,'b':1}),state('c',clock={'a':1,'b':1,'c':1})]
        q=qualify(subject(),states,lease(),NOW,expected(),deps()); self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertFalse(q.receipt.actuation_performed)
    def test_concurrent_majority_stays_unknown(self):
        states=[state('a',clock={'a':1}),state('b',clock={'b':1}),state('c',clock={'c':1})]
        self.assertEqual(qualify(subject(),states,lease(),NOW,expected(),deps()).standing,'UNKNOWN')
