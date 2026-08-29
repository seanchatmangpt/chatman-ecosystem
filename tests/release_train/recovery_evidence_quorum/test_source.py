import unittest
from scripts.release_train.recovery_evidence_quorum.source import EvidenceSource
class T(unittest.TestCase):
 def test_source(self): self.assertEqual(EvidenceSource("p","r","a","f").fingerprint,EvidenceSource("p","r","a","f").fingerprint)
 def test_empty(self):
  with self.assertRaises(ValueError): EvidenceSource("p","","a","f")
