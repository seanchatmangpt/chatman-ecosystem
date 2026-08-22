import unittest
from scripts.release_train.dependency_qualification import Refusal
from scripts.release_train.dependency_qualification.receipt import manufacture,replay
class T(unittest.TestCase):
 def test_replay_and_tamper(self):
  r=manufacture({'x':1}); replay(r); r['payload']['x']=2
  with self.assertRaises(Refusal): replay(r)
