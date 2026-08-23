import unittest
from scripts.release_train.replicated_policy_admission.authority import ActionClass,admit_action
from scripts.release_train.replicated_policy_admission.refusal import Refused
class TestAuthority(unittest.TestCase):
    def test_construct_admitted_do_refused(self):
        admit_action(ActionClass.CONSTRUCT)
        with self.assertRaises(Refused): admit_action(ActionClass.DO)
