import unittest
from scripts.release_train.consumer_promotion.authority import require
class T(unittest.TestCase):
 def test_no_do(self):
  self.assertEqual(require("CONSTRUCT"),"ADMITTED")
  with self.assertRaisesRegex(PermissionError,"BRCE_REQUIRED"): require("DO")
