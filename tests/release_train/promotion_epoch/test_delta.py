import unittest
from scripts.release_train.promotion_epoch.subject import Subject
from scripts.release_train.promotion_epoch.delta import EvidenceDelta,DeltaRefusal
class T(unittest.TestCase):
 def test_movement(self): self.assertTrue(EvidenceDelta(Subject("o/r","a"*40),Subject("o/r","b"*40),"PASS","PASS",True).changed)
 def test_contradiction(self):
  with self.assertRaises(DeltaRefusal): EvidenceDelta(Subject("o/r","a"*40),Subject("o/r","a"*40),"PASS","PASS",True)
