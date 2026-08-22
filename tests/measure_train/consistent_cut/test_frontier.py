import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consistent_cut.subject import Subject,Refused
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.frontier import current_frontier
class T(unittest.TestCase):
 def test_latest_generation(self):
  now=datetime.now(timezone.utc); s=Subject("o/r","a"*40)
  old=EpochStamp(s,1,"1"*64,now); new=EpochStamp(s,2,"2"*64,now+timedelta(seconds=1))
  self.assertEqual(current_frontier([old,new])[0],new)
