import unittest
from scripts.develop_train.ack_discharge.strategy import *
class T(unittest.TestCase):
 def test_distinct(self):
  xs=[FrontierItem('a',True,True),FrontierItem('b',True,False),FrontierItem('c',False,False)]
  self.assertFalse(is_complete(Strategy.ALL,xs));self.assertTrue(is_complete(Strategy.QUORUM,xs));self.assertTrue(is_complete(Strategy.CRITICAL_PATH,xs))
