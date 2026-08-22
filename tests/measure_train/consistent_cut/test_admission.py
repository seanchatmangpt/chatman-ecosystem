import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consistent_cut.subject import Subject,Refused
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.observation import Observation
from scripts.measure_train.consistent_cut.cut import ConsistentCut
from scripts.measure_train.consistent_cut.admission import admit_cut
class T(unittest.TestCase):
 def test_torn_observation_refuses(self):
  now=datetime.now(timezone.utc); p1=Subject("p/r","a"*40); p2=Subject("p/r","b"*40); c=Subject("c/r","c"*40)
  old=EpochStamp(p1,1,"1"*64,now); new=EpochStamp(p2,2,"2"*64,now+timedelta(seconds=1))
  obs=Observation(c,old,"REPOSITORY","PASS","e",now+timedelta(seconds=2))
  with self.assertRaises(Refused): admit_cut(ConsistentCut((new,)),(new,),(obs,))
