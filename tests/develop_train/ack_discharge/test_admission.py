import unittest
from datetime import datetime,timedelta,timezone
from scripts.develop_train.ack_discharge.admission import *
from scripts.develop_train.ack_discharge.event import *
from scripts.develop_train.ack_discharge.subject import Subject
from scripts.develop_train.ack_discharge.witness import *
class T(unittest.TestCase):
 def test_chain(self):
  t=datetime.now(timezone.utc);p=Subject('o/p','a'*40);c=Subject('o/c','b'*40);e=InvalidationEvent(p,InvalidationKind.NEW_HEAD,'e',t)
  d=Delivery('e',c,t+timedelta(seconds=1),'dr');a=Acknowledgement('e',c,t+timedelta(seconds=2),'dr');x=Discharge('e',c,t+timedelta(seconds=3),'ar',DischargeResult.REQUALIFIED,'er')
  self.assertEqual(admit_chain(e,d,a,x).discharge.result,DischargeResult.REQUALIFIED)
  with self.assertRaises(RefusedEvidence):admit_chain(e,d,Acknowledgement('e',c,t+timedelta(seconds=2),'bad'),x)
