import unittest
from scripts.release_train.promotion_intent_lease.cut import CutIdentity
from scripts.release_train.promotion_intent_lease.subject import Refusal
from _helpers import S2
class T(unittest.TestCase):
 def test_generation_and_unique(self):
  self.assertEqual(CutIdentity('x',0,(S2,)).generation,0)
  with self.assertRaisesRegex(Refusal,'INVALID_CUT_GENERATION'): CutIdentity('x',-1,(S2,))
  with self.assertRaisesRegex(Refusal,'INVALID_CUT_IDENTITY'): CutIdentity('x',1,(S2,S2))
