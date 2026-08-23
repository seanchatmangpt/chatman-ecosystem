import unittest
from scripts.release_train.sequential_horizon_admission.receipt import make_receipt,replay,Receipt
class T(unittest.TestCase):
 def test_receipt_is_no_actuation_and_tamper_sensitive(self):
  r=make_receipt({'authority':'SELECT','actuation_performed':False,'x':1})
  self.assertTrue(replay(r)); self.assertFalse(replay(Receipt({**r.body,'x':2},r.digest)))
