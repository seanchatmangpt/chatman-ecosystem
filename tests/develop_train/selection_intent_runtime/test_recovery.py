import unittest
from scripts.develop_train.selection_intent_runtime.recovery import *
from scripts.develop_train.selection_intent_runtime.drift import DriftKind
from scripts.develop_train.selection_intent_runtime.compatibility import *
class TestRecovery(unittest.TestCase):
 def test_three_recovery_paths(self):
  self.assertTrue(recover(RecoveryStrategy.RESELECT,DriftKind.POLICY).requires_new_proof)
  with self.assertRaisesRegex(ValueError,"INSUFFICIENT_EQUIVALENCE_WITNESS"): recover(RecoveryStrategy.REBIND_EQUIVALENT,DriftKind.POLICY)
  w=CompatibilityWitness(CompatibilityKind.SEMANTIC_EQUIVALENT,"a"*64,"b"*64,"e"); self.assertTrue(recover(RecoveryStrategy.REBIND_EQUIVALENT,DriftKind.POLICY,w).reusable); self.assertFalse(recover(RecoveryStrategy.REQUALIFY_COMPATIBLE,DriftKind.POLICY,w).reusable)
