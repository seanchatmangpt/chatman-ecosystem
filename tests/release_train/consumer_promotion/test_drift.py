import unittest
from scripts.release_train.consumer_promotion.drift import classify
class T(unittest.TestCase):
 def test_reasons(self):
  self.assertEqual(classify("a","b","v","v",True),"SUPERSEDED_RECEIPT")
  self.assertEqual(classify("a","a","v1","v2",True),"SCHEMA_DRIFT")
