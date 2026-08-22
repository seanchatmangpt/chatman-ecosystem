import unittest
from scripts.release_train.authority import ProposedAction, admit_actions, AuthorityRefusal

class AuthorityTests(unittest.TestCase):
    def test_select_construct_verify_admit(self):
        kinds=[x.kind for x in admit_actions([ProposedAction("SELECT","x"),ProposedAction("CONSTRUCT","y"),ProposedAction("VERIFY","z")])]
        self.assertEqual(kinds,["SELECT","CONSTRUCT","VERIFY"])
    def test_do_refuses(self):
        with self.assertRaisesRegex(AuthorityRefusal,"CONSEQUENTIAL_ACTION:DO"):
            admit_actions([ProposedAction("DO","azure")])
