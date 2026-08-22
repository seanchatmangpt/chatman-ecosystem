import unittest
from scripts.develop_train.recovery_evidence_quorum.provenance import ProvenanceGraph
from scripts.develop_train.recovery_evidence_quorum.subject import Refused

class TestProvenance(unittest.TestCase):
    def test_transitive_derivation_and_cycle_refusal(self):
        g=ProvenanceGraph(); g.add('c','b'); g.add('b','a')
        self.assertTrue(g.derives_from('c','a'))
        with self.assertRaisesRegex(Refused,'PROVENANCE_CYCLE'): g.add('a','c')
