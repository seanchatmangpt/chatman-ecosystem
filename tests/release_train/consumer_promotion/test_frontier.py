import unittest
from scripts.release_train.consumer_promotion.subject import Subject
from scripts.release_train.consumer_promotion.evidence import ProducerEvidence
from scripts.release_train.consumer_promotion.frontier import resolve
class T(unittest.TestCase):
 def test_diverged(self):
  s=Subject("o/r","a"*40); a=ProducerEvidence(s,"1"*64,"v","ALIVE","REPOSITORY"); b=ProducerEvidence(s,"2"*64,"v","ALIVE","REPOSITORY")
  self.assertTrue(resolve([a,b]).diverged)
