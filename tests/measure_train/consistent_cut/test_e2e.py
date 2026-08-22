import unittest
from datetime import datetime,timezone,timedelta
from scripts.measure_train.consistent_cut.subject import Subject
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.observation import Observation
from scripts.measure_train.consistent_cut.cut import ConsistentCut
from scripts.measure_train.consistent_cut.qualify import qualify
from scripts.measure_train.consistent_cut.replay import replay
class T(unittest.TestCase):
 def test_multi_producer_consistent_cut(self):
  now=datetime.now(timezone.utc); c=Subject("c/r","c"*40)
  a=EpochStamp(Subject("p/a","a"*40),2,"1"*64,now)
  b=EpochStamp(Subject("p/b","b"*40),7,"2"*64,now)
  observations=(
    Observation(c,a,"REPOSITORY","PASS","a1",now+timedelta(seconds=1)),
    Observation(c,b,"RUNTIME","PASS","b1",now+timedelta(seconds=1)),
  )
  q=qualify(c,(a,b),ConsistentCut((a,b)),observations)
  self.assertEqual(q["standing"],"PARTIAL_ALIVE")
  self.assertFalse(q["actuation_performed"])
  self.assertEqual(replay(q["receipt"]),"REPLAY_MATCH")
