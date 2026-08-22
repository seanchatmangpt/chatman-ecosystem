import unittest
from scripts.measure_train.consumer_binding.subject import Subject,Refused
from scripts.measure_train.consumer_binding.consumer import Consumer
class T(unittest.TestCase):
 def test_component(self):
  self.assertEqual(Consumer(Subject("o/r","a"*40),"release").component,"release")
  with self.assertRaises(Refused): Consumer(Subject("o/r","a"*40),"")
