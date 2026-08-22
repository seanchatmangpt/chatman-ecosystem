import unittest
from scripts.release_train.promotion_recovery.authority import *
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_do_refuses(self):
  self.assertEqual(require(ActionClass.CONSTRUCT),ActionClass.CONSTRUCT)
  with self.assertRaisesRegex(Refusal,'BRCE_REQUIRED'): require(ActionClass.DO)
