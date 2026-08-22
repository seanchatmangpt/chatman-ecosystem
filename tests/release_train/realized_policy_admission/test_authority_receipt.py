import unittest
from dataclasses import replace
from scripts.release_train.realized_policy_admission.authority import ActionClass,admit_action
from scripts.release_train.realized_policy_admission.receipt import issue,replay
class T(unittest.TestCase):
    def test_no_do_and_tamper(self):
        with self.assertRaisesRegex(PermissionError,"BRCE_REQUIRED"): admit_action(ActionClass.DO)
        r=issue({"x":1}); self.assertTrue(replay(r))
        self.assertFalse(replay(replace(r,body={**r.body,"actuation_performed":True})))
