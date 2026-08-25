import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.witness import Witness
from scripts.measure_train.requalification_epoch.census import census
from scripts.measure_train.requalification_epoch.standing import standing
class T(unittest.TestCase):
 def test_one_old_or_missing_consumer_keeps_unknown(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); c1=Subject("c/a","b"*40); c2=Subject("c/b","c"*40); e=InvalidationEpoch(p,2,"e2",now,"2"*64)
  d=Witness(c1,p,2,"e2","DELIVERY","d",now+timedelta(seconds=1)); a=Witness(c1,p,2,"e2","ACKNOWLEDGEMENT","a",now+timedelta(seconds=2),parent_id="d"); x=Witness(c1,p,2,"e2","DISCHARGE","x",now+timedelta(seconds=3),"REQUALIFIED","a")
  rows=census([c1,c2],e,[d,a,x]); self.assertIn((c2.repo,c2.sha,"PENDING_DELIVERY"),rows); self.assertEqual(standing(rows),"UNKNOWN")
