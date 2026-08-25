import unittest
from scripts.measure_train.consumer_binding.scope import scope_satisfies
class T(unittest.TestCase):
 def test_no_narrow_laundering(self):
  self.assertFalse(scope_satisfies("FOCUSED","REPOSITORY"))
  self.assertTrue(scope_satisfies("REPOSITORY","FOCUSED"))
