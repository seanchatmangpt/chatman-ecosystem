import unittest
from scripts.release_train.promotion_epoch.subject import Subject
from scripts.release_train.promotion_epoch.candidate import PromotionCandidate,CandidateRefusal
class T(unittest.TestCase):
 def test_candidate(self): self.assertEqual(PromotionCandidate("c",Subject("o/r","a"*40),Subject("o/r","b"*40),5,True,"ALIVE").component,"c")
 def test_irreversible_refuses(self):
  with self.assertRaises(CandidateRefusal): PromotionCandidate("c",Subject("o/r","a"*40),Subject("o/r","b"*40),5,False,"ALIVE")
