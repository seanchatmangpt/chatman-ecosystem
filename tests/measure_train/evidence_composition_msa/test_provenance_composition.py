import unittest
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.interval import Interval
from scripts.measure_train.evidence_composition_msa.provenance import ProvenanceWitness
from scripts.measure_train.evidence_composition_msa.composition import compose
from scripts.measure_train.evidence_composition_msa.subject import Refused
class T(unittest.TestCase):
 def test_dependence_modes_do_not_collapse(self):
  a=Interval(Fraction(7,10),Fraction(9,10)); b=Interval(Fraction(7,10),Fraction(9,10))
  c=compose(a,b,"UNKNOWN_DEPENDENCE")
  i=compose(a,b,"INDEPENDENT",ProvenanceWitness("a","b",True,True,True))
  self.assertNotEqual(c,i)
  with self.assertRaises(Refused): compose(a,b,"INDEPENDENT",ProvenanceWitness("a","b",True,False,True))
