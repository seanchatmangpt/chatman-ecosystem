import unittest
from scripts.release_train.feedback_policy_admission.receipt import manufacture,replay,Receipt
from scripts.release_train.feedback_policy_admission.errors import Refused
class T(unittest.TestCase):
 def test_replay_tamper(self):
  r=manufacture({"actuation_performed":False,"x":1})
  self.assertTrue(replay(r))
  with self.assertRaises(Refused): replay(Receipt({"actuation_performed":False,"x":2},r.digest))
  with self.assertRaises(Refused): manufacture({"actuation_performed":True})
if __name__=="__main__": unittest.main()
