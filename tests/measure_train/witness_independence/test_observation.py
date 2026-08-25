import unittest
from datetime import datetime,timezone
from scripts.measure_train.witness_independence.subject import Subject,Refused
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
class T(unittest.TestCase):
 def test_scope_time(self):
  s=Subject("o/r","a"*40); src=EvidenceSource("RUNTIME","p","","","x")
  self.assertEqual(WitnessObservation(s,src,"REPOSITORY","PASS","e",datetime.now(timezone.utc)).outcome,"PASS")
  with self.assertRaises(Refused): WitnessObservation(s,src,"BAD","PASS","x",datetime.now(timezone.utc))
