import unittest
from scripts.develop_train.process_transition_substrate import *
class T(unittest.TestCase):
 def test_tls_contradiction(self):
  with self.assertRaises(Refused): RuntimeReceipt("global over inet_tls","inet_tcp",False,0,"d"*64).admit()
 def test_multi_engine(self):
  a=ProjectionWitness("BEAM","e"*64,frozenset({"trace","receipt"}),"f"*64)
  b=ProjectionWitness("WASM","e"*64,frozenset({"trace","receipt"}),"f"*64)
  self.assertTrue(require_equivalent([a,b]))
