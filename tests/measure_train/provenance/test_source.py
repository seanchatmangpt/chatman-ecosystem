import unittest
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.subject import Refused
class T(unittest.TestCase):
 def test_kind(self):
  self.assertEqual(Source("GITHUB_ACTION","run:1").kind,"GITHUB_ACTION")
  with self.assertRaises(Refused): Source("BAD","x")
