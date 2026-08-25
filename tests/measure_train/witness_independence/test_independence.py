import unittest
from datetime import datetime,timezone
from scripts.measure_train.witness_independence.subject import Subject,Refused
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.independence import relation,assert_independent
class T(unittest.TestCase):
 def test_shared_run_is_correlated(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  a=WitnessObservation(s,EvidenceSource("WORKFLOW","p","run","","a"),"REPOSITORY","PASS","a",now)
  b=WitnessObservation(s,EvidenceSource("STATUS","q","run","","b"),"REPOSITORY","PASS","b",now)
  self.assertEqual(relation(a,b),"CORRELATED")
  with self.assertRaises(Refused): assert_independent(a,b)
