import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.advisory import AdvisoryFinding, admit_advisories
class T(unittest.TestCase):
 def test_refuses_live(self):
  with self.assertRaises(Refusal): admit_advisories([AdvisoryFinding('RUSTSEC-2024-0370','proc-macro-error','unmaintained')])
 def test_clean(self): self.assertEqual(len(admit_advisories([AdvisoryFinding('X','x','resolved')])),1)
