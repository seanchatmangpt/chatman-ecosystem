import unittest
from datetime import datetime,timezone
from scripts.measure_train.provenance.subject import Subject,Refused
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.claim import Claim
class T(unittest.TestCase):
 def test_claim(self):
  c=Claim(Subject("o/r","a"*40),Source("RUNTIME","x"),datetime.now(timezone.utc),"PASS","e1")
  self.assertEqual(c.outcome,"PASS")
  with self.assertRaises(Refused): Claim(c.subject,c.source,datetime.now(),"PASS","e2")
