import unittest
from scripts.release_train.promotion_intent_lease.authority import require,ActionClass
from scripts.release_train.promotion_intent_lease.subject import Refusal
class T(unittest.TestCase):
 def test_do_refused(self):
  require(ActionClass.CONSTRUCT)
  with self.assertRaisesRegex(Refusal,'BRCE_REQUIRED'): require(ActionClass.DO)
