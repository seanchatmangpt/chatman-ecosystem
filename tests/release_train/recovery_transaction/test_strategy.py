import unittest
from scripts.release_train.recovery_transaction import *
H='a'*64
class T(unittest.TestCase):
 def test_three_strategies(self):
  exact=CompatibilityWitness(H,H,WitnessKind.EXACT,H,True)
  self.assertFalse(decide('CAS_RESELECT',None).reuses_prior_selection);self.assertTrue(decide('VALIDATE_REBIND',exact).reuses_prior_selection);self.assertEqual(decide('REQUALIFY_ONLY',None).standing,'REQUALIFYING')
 def test_unknown(self):
  with self.assertRaisesRegex(Refusal,'UNKNOWN'):decide('MAGIC',None)
if __name__=='__main__':unittest.main()
