import unittest
from scripts.measure_train.decision_realization_transport_msa.subject import Subject
from scripts.measure_train.decision_realization_transport_msa.frontier import TransportModel
from scripts.measure_train.decision_realization_transport_msa.standing import standing
from scripts.measure_train.decision_realization_transport_msa.receipt import manufacture
from scripts.measure_train.decision_realization_transport_msa.replay import replay
from scripts.measure_train.decision_realization_transport_msa.errors import Refused
class T(unittest.TestCase):
 def test_ceiling_and_tamper(self):
  m=TransportModel("A","B",1,"c"*64,True)
  self.assertEqual(standing(m,1,10,0.1,False),"PARTIAL_ALIVE")
  r=manufacture(Subject("o/r","a"*40,"b"*64),m,"PARTIAL_ALIVE",{"x":1})
  self.assertEqual(replay(r),"REPLAY_MATCH");r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused):replay(r)
