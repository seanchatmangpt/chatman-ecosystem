import unittest
from fractions import Fraction
from scripts.measure_train.validation_independence_realization_msa.graph import Evidence,admit_graph
from scripts.measure_train.validation_independence_realization_msa.overlap import ancestry_overlap
from scripts.measure_train.validation_independence_realization_msa.empirical import measure_pairs
class T(unittest.TestCase):
 def test_shared_root_and_dependence(self):
  g=admit_graph([Evidence("r",(),0,"a"*64),Evidence("x",("r",),1,"b"*64),Evidence("y",("r",),1,"c"*64)])
  self.assertGreater(ancestry_overlap(g,"x","y"),Fraction(0))
  st=measure_pairs([(0,0),(0,0),(1,1),(1,1)])
  self.assertGreater(st.phi,0.9)
