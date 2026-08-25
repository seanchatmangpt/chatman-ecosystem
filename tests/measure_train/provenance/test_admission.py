import unittest
from datetime import datetime,timezone
from scripts.measure_train.provenance.subject import Subject,Refused
from scripts.measure_train.provenance.source import Source
from scripts.measure_train.provenance.claim import Claim
from scripts.measure_train.provenance.admission import admit_claims
class T(unittest.TestCase):
 def test_foreign(self):
  a,b=Subject("o/r","a"*40),Subject("o/r","b"*40); s=Source("GITHUB_ACTION","r")
  c=Claim(b,s,datetime.now(timezone.utc),"PASS","e")
  with self.assertRaises(Refused): admit_claims(a,[c])
