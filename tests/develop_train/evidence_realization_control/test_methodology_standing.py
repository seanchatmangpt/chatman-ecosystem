import unittest
from scripts.develop_train.evidence_realization_control import *
class T(unittest.TestCase):
 def test_methodology(self): self.assertTrue(require_closure(REQUIRED))
 def test_missing(self):
  with self.assertRaises(Refused): require_closure(REQUIRED-{'simulation'})
 def test_failure_dominates(self): self.assertEqual(combine(['PARTIAL_ALIVE','BUILD_BROKEN']),'BUILD_BROKEN')
