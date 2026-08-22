import unittest
from scripts.develop_train.ack_discharge.receipt import *
from scripts.develop_train.ack_discharge.strategy import Strategy
class T(unittest.TestCase):
 def test_tamper(self):
  r=QualificationReceipt('o/p@'+'a'*40,'e',Strategy.ALL,[],'UNKNOWN','x');d=digest(r);self.assertTrue(replay(r,d));self.assertFalse(replay(QualificationReceipt(r.producer,r.event_id,Strategy.QUORUM,[],'UNKNOWN','x'),d))
