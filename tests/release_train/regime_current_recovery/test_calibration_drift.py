import unittest
from fractions import Fraction
from scripts.release_train.regime_current_recovery.drift import compare_models,classify_l1
from fixtures import model
class T(unittest.TestCase):
 def test_drift(self):
  v=compare_models(model('s1',0),model('s1',2)); self.assertGreater(v.l1,0); self.assertEqual(classify_l1(v,Fraction(1,10)),'DRIFT')
 def test_stable(self): self.assertEqual(compare_models(model(),model()).l1,0)
