import unittest
from scripts.release_train.promotion_epoch.subject import Subject
from scripts.release_train.promotion_epoch.candidate import PromotionCandidate
from scripts.release_train.promotion_epoch.policy import admit_candidate,PolicyRefusal
C=PromotionCandidate("c",Subject("o/r","a"*40),Subject("o/r","b"*40),5,True,"ALIVE")
class T(unittest.TestCase):
 def test_admit(self): self.assertIs(admit_candidate(C,True,True,True),C)
 def test_advisory_refuses(self):
  with self.assertRaises(PolicyRefusal): admit_candidate(C,True,True,False)
