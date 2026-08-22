import unittest
from datetime import datetime
from scripts.measure_train.invalidation_ack.subject import Subject,Refused
from scripts.measure_train.invalidation_ack.delivery import Delivery
class T(unittest.TestCase):
 def test_naive_refuses(self):
  with self.assertRaises(Refused): Delivery("e",Subject("o/r","a"*40),datetime.now(),"d")
