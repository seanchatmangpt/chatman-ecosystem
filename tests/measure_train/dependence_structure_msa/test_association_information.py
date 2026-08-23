import unittest
from datetime import datetime,timezone
from scripts.measure_train.dependence_structure_msa.subject import Subject
from scripts.measure_train.dependence_structure_msa.observation import PairObservation
from scripts.measure_train.dependence_structure_msa.contingency import contingency
from scripts.measure_train.dependence_structure_msa.association import association
from scripts.measure_train.dependence_structure_msa.information import profile
class T(unittest.TestCase):
 def test_perfect_dependence(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[PairObservation(s,"L","R",str(i),v,v,"all",now) for i,v in enumerate([0,1]*4)]
  t=contingency(rows)
  self.assertAlmostEqual(association(t).absolute_phi,1.0)
  self.assertAlmostEqual(profile(t).mutual_information_bits,1.0)
