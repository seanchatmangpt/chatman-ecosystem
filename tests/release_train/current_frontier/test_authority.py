import unittest
from scripts.release_train.current_frontier.authority import require, Refusal
class T(unittest.TestCase):
 def test_construct_allowed(self): require("CONSTRUCT")
 def test_do_refuses(self):
  with self.assertRaises(Refusal): require("DO")
