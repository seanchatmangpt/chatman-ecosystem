import unittest
from datetime import datetime,timezone
from scripts.measure_train.consistent_cut.subject import Subject,Refused
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.cut import ConsistentCut
class T(unittest.TestCase):
 def test_duplicate_repo_refuses(self):
  now=datetime.now(timezone.utc)
  a=EpochStamp(Subject("o/r","a"*40),1,"1"*64,now)
  b=EpochStamp(Subject("o/r","b"*40),2,"2"*64,now)
  with self.assertRaises(Refused): ConsistentCut((a,b))
