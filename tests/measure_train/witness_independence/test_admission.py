import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.witness_independence.subject import Subject,Refused
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.admission import admit
class T(unittest.TestCase):
 def test_foreign_and_future_refuse(self):
  now=datetime.now(timezone.utc); a=Subject("o/r","a"*40); b=Subject("o/r","b"*40)
  src=EvidenceSource("RUNTIME","p","","","s")
  with self.assertRaises(Refused): admit(a,[WitnessObservation(b,src,"REPOSITORY","PASS","x",now)],[],now)
  with self.assertRaises(Refused): admit(a,[WitnessObservation(a,src,"REPOSITORY","PASS","y",now+timedelta(seconds=1))],[],now)
