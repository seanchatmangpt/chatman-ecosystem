import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.witness_independence.subject import Subject
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.diversity import effective_source_count
class T(unittest.TestCase):
 def test_inverse_simpson_exact(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc); ps=["a","a","b"]
  rows=[WitnessObservation(s,EvidenceSource("RUNTIME",p,str(i),"","s"+str(i)),"REPOSITORY","PASS",str(i),now) for i,p in enumerate(ps)]
  self.assertEqual(effective_source_count(rows),Fraction(9,5))
