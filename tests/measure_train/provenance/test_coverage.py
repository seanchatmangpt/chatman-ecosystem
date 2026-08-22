import unittest
from datetime import datetime,timezone
from scripts.measure_train.provenance.subject import Subject
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.claim import Claim
from scripts.measure_train.provenance.coverage import provenance_coverage
class T(unittest.TestCase):
 def test_missing_blocks_positive(self):
  s=Subject("o/r","a"*40); c=Claim(s,Source("RUNTIME","x"),datetime.now(timezone.utc),"PASS","e")
  self.assertEqual(provenance_coverage([c],[])["standing"],"UNKNOWN")
