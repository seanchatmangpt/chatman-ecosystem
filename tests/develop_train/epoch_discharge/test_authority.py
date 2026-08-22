import unittest
from scripts.develop_train.epoch_discharge.authority import ActionClass,admit_action
class T(unittest.TestCase):
 def test_do_refuses(self):
  with self.assertRaisesRegex(PermissionError,"BRCE_REQUIRED"): admit_action(ActionClass.DO)
  admit_action(ActionClass.CONSTRUCT)
