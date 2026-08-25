import unittest
from scripts.measure_train.delta.identity_delta import HeadDelta
class T(unittest.TestCase):
 def test_movement_and_short_sha_refusal(self):
  self.assertTrue(HeadDelta("o/r","a"*40,"b"*40).moved)
  with self.assertRaises(ValueError): HeadDelta("o/r","abc","b"*40)
