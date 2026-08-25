import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.requalification_epoch.subject import Subject,Refused
from scripts.measure_train.requalification_epoch.epoch import InvalidationEpoch
from scripts.measure_train.requalification_epoch.frontier import resolve_epoch_frontier
class T(unittest.TestCase):
 def test_latest_generation_wins_and_divergence_refuses(self):
  now=datetime.now(timezone.utc); p=Subject("p/r","a"*40); a=InvalidationEpoch(p,1,"e1",now,"1"*64); b=InvalidationEpoch(p,2,"e2",now+timedelta(seconds=1),"2"*64)
  self.assertEqual(resolve_epoch_frontier([a,b])[p],b)
  c=InvalidationEpoch(p,2,"other",now+timedelta(seconds=2),"3"*64)
  with self.assertRaises(Refused): resolve_epoch_frontier([b,c])
