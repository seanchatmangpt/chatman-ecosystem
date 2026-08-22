import unittest
from scripts.release_train.coherent_epoch_promotion.authority import require
class T(unittest.TestCase):
 def test_do_refuses(self):
  require('CONSTRUCT')
  with self.assertRaisesRegex(PermissionError,'BRCE_REQUIRED'): require('DO')
