import unittest
from scripts.develop_train.ack_discharge.authority import *
class T(unittest.TestCase):
 def test_do_refused(self):
  require_nonconsequential(ActionClass.CONSTRUCT)
  with self.assertRaises(RefusedAuthority):require_nonconsequential(ActionClass.DO)
