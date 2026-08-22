import unittest
from scripts.release_train.regime_current_recovery.receipt import manufacture,replay,Receipt
from scripts.release_train.regime_current_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_tamper(self):
  a=manufacture({'x':1}); b=manufacture({'x':1}); self.assertEqual(a,b); self.assertTrue(replay(a)); self.assertFalse(replay(Receipt({**a.body,'x':2},a.digest)))
 def test_authority(self):
  a=manufacture({'x':1})
  with self.assertRaisesRegex(Refusal,'AUTHORITY_DRIFT'): replay(Receipt({**a.body,'actuation_performed':True},a.digest))
