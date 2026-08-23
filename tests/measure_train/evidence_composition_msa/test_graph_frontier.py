import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject,Refused
from scripts.measure_train.evidence_composition_msa.interval import Interval
from scripts.measure_train.evidence_composition_msa.evidence import EvidenceNode
from scripts.measure_train.evidence_composition_msa.graph import admit_graph
from scripts.measure_train.evidence_composition_msa.frontier import current_frontier
class T(unittest.TestCase):
 def node(self,e,g):
  return EvidenceNode(Subject("o/r","a"*40,"b"*64),e,"RUNTIME",g,Interval(Fraction(1,2),Fraction(1)),"c"*64,"d"*64,"x",datetime.now(timezone.utc))
 def test_cycle_and_split_refuse(self):
  a,b=self.node("a",1),self.node("b",2)
  self.assertEqual(current_frontier([a,b])[0],b)
  with self.assertRaises(Refused): admit_graph([a,b],[("a","b"),("b","a")])
