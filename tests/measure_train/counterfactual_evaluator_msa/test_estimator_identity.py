import unittest
from scripts.measure_train.counterfactual_evaluator_msa.estimator import EstimatorIdentity
from scripts.measure_train.counterfactual_evaluator_msa.refusal import Refused
class T(unittest.TestCase):
 def test_model_provenance(self):
  EstimatorIdentity("ips","IPS","1"*64)
  with self.assertRaises(Refused): EstimatorIdentity("dm","DIRECT_MODEL","2"*64)
