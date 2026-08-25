import unittest
from scripts.measure_train.provenance.subject import Subject
from scripts.measure_train.provenance.receipt import manufacture_receipt
class T(unittest.TestCase):
 def test_deterministic(self):
  s=Subject("o/r","a"*40); a=manufacture_receipt(s,{"standing":"UNKNOWN"},(),None); b=manufacture_receipt(s,{"standing":"UNKNOWN"},(),None)
  self.assertEqual(a,b); self.assertFalse(a["body"]["actuation_performed"])
