import unittest
from scripts.release_train.consumer_promotion.candidate import Candidate,select
class T(unittest.TestCase):
 def test_deterministic(self):
  x=select([Candidate("b",3,3,True),Candidate("a",3,3,True)]); self.assertEqual(x.name,"a")
