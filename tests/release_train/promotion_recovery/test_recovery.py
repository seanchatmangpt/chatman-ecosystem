import unittest
from scripts.release_train.promotion_recovery.recovery import *
from scripts.release_train.promotion_recovery.drift import DriftKind
from scripts.release_train.promotion_recovery.compatibility import *
from scripts.release_train.promotion_recovery.subject import Refusal
class T(unittest.TestCase):
 def test_recovery_preserves_three_paths(self):
  w=CompatibilityWitness(CompatibilityKind.BACKWARD_COMPATIBLE,'a'*64,'b'*64,'e')
  self.assertEqual(recover(DriftKind.POLICY,w,RecoveryStrategy.RESELECT).standing,'REQUALIFYING')
  with self.assertRaisesRegex(Refusal,'INSUFFICIENT_EQUIVALENCE'): recover(DriftKind.POLICY,w,RecoveryStrategy.REBIND_EQUIVALENT)
  self.assertEqual(recover(DriftKind.POLICY,w,RecoveryStrategy.REQUALIFY_COMPATIBLE).standing,'REQUALIFYING')
