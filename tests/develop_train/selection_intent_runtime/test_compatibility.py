import unittest
from scripts.develop_train.selection_intent_runtime.compatibility import *
class TestCompatibility(unittest.TestCase):
 def test_false_exact_refuses(self):
  with self.assertRaisesRegex(ValueError,"FALSE_EXACT_EQUIVALENCE"): CompatibilityWitness(CompatibilityKind.EXACT,"a"*64,"b"*64,"e")
  self.assertTrue(CompatibilityWitness(CompatibilityKind.SEMANTIC_EQUIVALENT,"a"*64,"b"*64,"e").evidence_id)
