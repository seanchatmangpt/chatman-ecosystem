import unittest
from scripts.develop_train.process_trace_correspondence import *
from scripts.develop_train.process_trace_correspondence.oracle import admit
from scripts.develop_train.process_trace_correspondence.correspondence import admit as corr
class T(unittest.TestCase):
 def test_oracle_independence(self):
  a=OracleWitness("a","i1","s","m","t"); b=OracleWitness("b","i2","s","m","t"); self.assertTrue(admit(a,b))
  with self.assertRaises(Refused): admit(a,OracleWitness("b","i1","s","m","t"))
 def test_rail_trace_divergence(self):
  es=[RailEvidence(r,"s","m","t",1) for r in Rail]; self.assertEqual(len(corr(es).rails),len(Rail))
  es[-1]=RailEvidence(Rail.CI,"s","m","different",1)
  with self.assertRaises(Refused): corr(es)
