import unittest
from scripts.measure_train.dependence_structure_msa.dependence_graph import components
from scripts.measure_train.dependence_structure_msa.hypergraph import triple_synergy
class T(unittest.TestCase):
 def test_clusters_and_xor_synergy(self):
  self.assertIn(("a","b","c"),components([("a","b","DEPENDENT"),("b","c","DEPENDENT"),("d","e","INDEPENDENT")]))
  rows=[]
  for x in (0,1):
   for y in (0,1):
    rows.append((x,y,x^y))
  s=triple_synergy(rows)
  self.assertGreater(s.higher_order_excess_bits,0.5)
