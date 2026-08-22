import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consistent_cut.subject import Subject
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.observation import Observation
from scripts.measure_train.consistent_cut.cut import ConsistentCut
from scripts.measure_train.consistent_cut.coherence import detect_torn_cut
class T(unittest.TestCase):
 def test_detects_torn(self):
  now=datetime.now(timezone.utc); c=Subject("c/r","c"*40)
  old=EpochStamp(Subject("p/r","a"*40),1,"1"*64,now); new=EpochStamp(Subject("p/r","b"*40),2,"2"*64,now)
  o=Observation(c,old,"REPOSITORY","PASS","e",now+timedelta(seconds=1))
  self.assertEqual(detect_torn_cut(ConsistentCut((new,)),[o]),("e",))
