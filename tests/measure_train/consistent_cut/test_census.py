import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consistent_cut.subject import Subject
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.observation import Observation
from scripts.measure_train.consistent_cut.census import census
class T(unittest.TestCase):
 def test_failure_dominates(self):
  now=datetime.now(timezone.utc); p=EpochStamp(Subject("p/r","a"*40),1,"1"*64,now); c=Subject("c/r","b"*40)
  rows=[Observation(c,p,"REPOSITORY","PASS","a",now+timedelta(seconds=1)),Observation(c,p,"REPOSITORY","FAIL","b",now+timedelta(seconds=1))]
  self.assertEqual(census(rows)[0][2],"FAIL")
