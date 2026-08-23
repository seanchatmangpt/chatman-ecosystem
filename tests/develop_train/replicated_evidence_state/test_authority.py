import unittest
from scripts.develop_train.replicated_evidence_state.authority import ActionClass, admit_action
from scripts.develop_train.replicated_evidence_state.errors import Refused

class AuthorityTest(unittest.TestCase):
    def test_do_requires_brce(self):
        admit_action(ActionClass.CONSTRUCT)
        with self.assertRaises(Refused): admit_action(ActionClass.DO)
