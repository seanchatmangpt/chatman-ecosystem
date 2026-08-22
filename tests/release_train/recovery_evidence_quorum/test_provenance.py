import unittest
from scripts.release_train.recovery_evidence_quorum.provenance import ProvenanceGraph
class T(unittest.TestCase):
 def test_transitive(self): self.assertTrue(ProvenanceGraph([("a","b"),("b","c")]).derives("a","c"))
 def test_cycle(self):
  with self.assertRaisesRegex(ValueError,"PROVENANCE_CYCLE"): ProvenanceGraph([("a","b"),("b","a")])
