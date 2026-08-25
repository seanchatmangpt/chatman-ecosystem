import unittest
from scripts.measure_train.decision_realization_transport_msa.frontier import TransportModel,current
from scripts.measure_train.decision_realization_transport_msa.errors import Refused
class T(unittest.TestCase):
 def test_split_frontier(self):
  a=TransportModel("A","B",1,"a"*64,True);b=TransportModel("A","B",1,"b"*64,True)
  with self.assertRaises(Refused): current([a,b])
