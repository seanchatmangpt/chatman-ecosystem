import unittest
from scripts.release_train.recovery_evidence_quorum.diversity import effective_source_diversity
class T(unittest.TestCase):
 def test_exact(self): self.assertEqual(effective_source_diversity(((1,2),(3,))),(9,5))
