import unittest
from scripts.measure_train.consumer_binding.subject import Subject
from scripts.measure_train.consumer_binding.producer import ProducerEvidence
from scripts.measure_train.consumer_binding.frontier import producer_frontier
class T(unittest.TestCase):
 def test_divergence(self):
  s=Subject("o/r","a"*40)
  rows=[ProducerEvidence(s,"1"*64,"x","PARTIAL_ALIVE"),ProducerEvidence(s,"2"*64,"x","PARTIAL_ALIVE")]
  self.assertEqual(producer_frontier(rows)["state"],"DIVERGED")
