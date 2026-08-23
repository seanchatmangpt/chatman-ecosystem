import unittest
from scripts.measure_train.counterfactual_evaluator_msa.estimator import EstimatorIdentity
from scripts.measure_train.counterfactual_evaluator_msa.independence import IndependenceProof,require_independent
from scripts.measure_train.counterfactual_evaluator_msa.refusal import Refused
class T(unittest.TestCase):
 def test_explicit_and_shared_impl(self):
  a=EstimatorIdentity("ips","IPS","1"*64); b=EstimatorIdentity("snips","SNIPS","2"*64)
  self.assertTrue(require_independent(a,b,[IndependenceProof("ips","snips","p")]))
  c=EstimatorIdentity("clip","CLIPPED_IPS","1"*64)
  with self.assertRaises(Refused): require_independent(a,c,[IndependenceProof("ips","clip","p")])
