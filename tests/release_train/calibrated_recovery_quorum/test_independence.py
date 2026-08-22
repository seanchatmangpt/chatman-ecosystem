import unittest
from scripts.release_train.calibrated_recovery_quorum.source import EvidenceSource
from scripts.release_train.calibrated_recovery_quorum.independence import *
class T(unittest.TestCase):
 def test_correlation_and_proof(self):
  a=EvidenceSource("p","r1","a1","f"); b=EvidenceSource("q","r2","a2","f")
  self.assertEqual(relation(a,b),"CORRELATED")
  self.assertEqual(relation(a,b,[IndependenceProof(a.fingerprint,b.fingerprint,True)]),"INDEPENDENT")
