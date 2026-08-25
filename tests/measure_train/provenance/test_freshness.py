import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.provenance.subject import Subject
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.claim import Claim
from scripts.measure_train.provenance.freshness import classify_freshness
class T(unittest.TestCase):
 def test_stale(self):
  now=datetime.now(timezone.utc); c=Claim(Subject("o/r","a"*40),Source("RUNTIME","x"),now-timedelta(seconds=5),"PASS","e")
  self.assertEqual(classify_freshness(c,now,1),"STALE")
