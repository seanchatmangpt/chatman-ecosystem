import unittest
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.subject import Refused
class T(unittest.TestCase):
 def test_digest(self):
  s=EvidenceSource("WORKFLOW","gha","1","a"*64,"s")
  self.assertIn("run:1",s.fingerprints())
  with self.assertRaises(Refused): EvidenceSource("BAD","x","","","s")
