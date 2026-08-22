import unittest
from scripts.release_train.promotion_recovery.compatibility import *
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_false_exact_refuses(self):
  with self.assertRaisesRegex(Refusal,'FALSE_EXACT_COMPATIBILITY'): CompatibilityWitness(CompatibilityKind.EXACT,'a'*64,'b'*64,'e')
