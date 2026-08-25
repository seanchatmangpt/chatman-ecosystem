import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.qualify import qualify
from scripts.measure_train.requalification_epoch.replay import replay
class T(unittest.TestCase):
 def test_new_epoch_requires_new_full_discharge(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c1=Subject("c/a","b"*40); c2=Subject("c/b","c"*40); e=InvalidationEpoch(p,3,"e3",now,"3"*64)
  ws=[]
  for i,c in enumerate((c1,c2)):
   d=Witness(c,p,3,"e3","DELIVERY",f"d{i}",now+timedelta(seconds=1)); a=Witness(c,p,3,"e3","ACKNOWLEDGEMENT",f"a{i}",now+timedelta(seconds=2),parent_id=f"d{i}"); ws += [d,a]
  ws.append(Witness(c1,p,3,"e3","DISCHARGE","x1",now+timedelta(seconds=3),"REQUALIFIED","a0"))
  q=qualify(e,[c1,c2],ws); self.assertEqual(q["standing"],"UNKNOWN"); self.assertFalse(q["actuation_performed"]); self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
  old=Witness(c2,p,2,"e2","DISCHARGE","old",now+timedelta(seconds=3),"REQUALIFIED","old-a")
  with self.assertRaisesRegex(Refused,"STALE_INVALIDATION_EPOCH"): qualify(e,[c1,c2],ws+[old])
