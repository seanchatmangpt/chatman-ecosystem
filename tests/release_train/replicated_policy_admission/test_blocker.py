import unittest
from fixtures import state,subject,lease,expected,deps,NOW
from scripts.release_train.replicated_policy_admission.engine import qualify
class TestBlocker(unittest.TestCase):
    def test_dependency_red_dominates(self):
        states=[state('a',clock={'a':1}),state('b',clock={'a':1,'b':1}),state('c',clock={'a':1,'b':1,'c':1})]
        self.assertEqual(qualify(subject(),states,lease(),NOW,expected(),deps('BUILD_BROKEN')).standing,'BLOCKED')
