import unittest
from fractions import Fraction as F
from scripts.release_train.outcome_capital_transport import Population,TransportModel,admit_transport,Refused
from scripts.release_train.outcome_capital_transport.shift import total_variation,jensen_shannon

class T(unittest.TestCase):
 def test_transport(self):
  s=Population("s",(("a",F(1,2)),("b",F(1,2)))); t=Population("t",(("a",F(2,3)),("b",F(1,3))))
  self.assertEqual(total_variation(s,t),F(1,6)); self.assertGreaterEqual(jensen_shannon(s,t),0)
  q=admit_transport(s,t,TransportModel(1,"d"),["a","b","a","b"]); self.assertGreaterEqual(q["ess"],2)
  bad=Population("bad",(("c",F(1)),))
  with self.assertRaises(Refused): admit_transport(s,bad,TransportModel(1,"d"),["a"])
