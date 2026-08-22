import unittest
from scripts.measure_train.witness_independence.standing import IndependencePolicy,evaluate
class T(unittest.TestCase):
 def test_two_independent_required(self):
  p=IndependencePolicy(2,"REPOSITORY")
  one=({"cluster_id":"a","members":("a",),"scopes":("REPOSITORY",),"state":"PASS"},)
  two=one+({"cluster_id":"b","members":("b",),"scopes":("REPOSITORY",),"state":"PASS"},)
  self.assertEqual(evaluate(one,p),"UNKNOWN")
  self.assertEqual(evaluate(two,p),"PARTIAL_ALIVE")
