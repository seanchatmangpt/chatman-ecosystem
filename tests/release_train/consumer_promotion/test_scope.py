import unittest
from scripts.release_train.consumer_promotion.scope import covers
class T(unittest.TestCase):
 def test_lattice(self):
  self.assertTrue(covers("REPOSITORY","FOCUSED")); self.assertFalse(covers("FOCUSED","REPOSITORY"))
