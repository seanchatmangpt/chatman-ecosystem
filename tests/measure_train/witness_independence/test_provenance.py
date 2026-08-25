import unittest
from datetime import datetime,timezone
from scripts.measure_train.witness_independence.subject import Subject,Refused
from scripts.measure_train.witness_independence.source import EvidenceSource
from scripts.measure_train.witness_independence.observation import WitnessObservation
from scripts.measure_train.witness_independence.provenance import ProvenanceEdge,validate_acyclic
class T(unittest.TestCase):
 def test_cycle_refuses(self):
  s=Subject("o/r","a"*40); now=datetime.now(timezone.utc)
  rows=[WitnessObservation(s,EvidenceSource("RUNTIME",x,"","","s"+x),"REPOSITORY","PASS",x,now) for x in ("a","b")]
  es=[ProvenanceEdge("a","b","DERIVED_FROM"),ProvenanceEdge("b","a","DERIVED_FROM")]
  with self.assertRaises(Refused): validate_acyclic(rows,es)
