import unittest
from scripts.measure_train.compatibility.subject_vector import Subject
from scripts.measure_train.compatibility.receipt import make_receipt
class T(unittest.TestCase):
 def test_deterministic(self):
  s=Subject("a/b","a"*40); self.assertEqual(make_receipt(s,"PARTIAL_ALIVE",["b","a"])["digest"],make_receipt(s,"PARTIAL_ALIVE",["a","b"])["digest"])
