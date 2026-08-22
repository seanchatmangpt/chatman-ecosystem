import unittest
from fractions import Fraction
from scripts.develop_train.evidence_acquisition_runtime.subject import Subject,Refusal
from scripts.develop_train.evidence_acquisition_runtime.candidate import EvidenceCandidate
class T(unittest.TestCase):
 def test_identity_and_authority(self):
  self.assertEqual(Subject('o/r','a'*40).key,'o/r@'+'a'*40)
  self.assertEqual(len(EvidenceCandidate('r','f','d','s',Fraction(1,2),10).fingerprint),64)
  with self.assertRaisesRegex(Refusal,'INEXACT'): Subject('o/r','main')
  with self.assertRaisesRegex(Refusal,'BRCE'): EvidenceCandidate('r','f','d','s',Fraction(),0,'DO')
