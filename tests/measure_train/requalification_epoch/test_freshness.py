import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.freshness import classify_freshness
class T(unittest.TestCase):
 def test_stale_and_future_are_distinct(self):
  now=datetime.now(timezone.utc); e=InvalidationEpoch(Subject("p/r","a"*40),1,"e",now-timedelta(seconds=5),"1"*64)
  self.assertEqual(classify_freshness(e,now,1),"STALE")
  future=InvalidationEpoch(e.producer,2,"e2",now+timedelta(seconds=1),"2"*64)
  with self.assertRaisesRegex(Refused,"FUTURE_EVIDENCE"): classify_freshness(future,now,1)
