import unittest
from scripts.measure_train.process_intelligence_correspondence_msa.oracle import OracleWitness,independent_agreement
from scripts.measure_train.process_intelligence_correspondence_msa.subject import Refused
class T(unittest.TestCase):
 def test_independence(self):
  a=OracleWitness("a","1"*64,"a"*40,"b"*64,"PASS")
  with self.assertRaises(Refused): independent_agreement([a,a])
