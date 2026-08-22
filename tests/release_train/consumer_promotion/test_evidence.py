import unittest
from scripts.release_train.consumer_promotion.subject import Subject
from scripts.release_train.consumer_promotion.evidence import ProducerEvidence
class T(unittest.TestCase):
 def test_receipt(self):
  with self.assertRaisesRegex(ValueError,"INVALID_RECEIPT"): ProducerEvidence(Subject("o/r","a"*40),"x","s","ALIVE","REPOSITORY")
