import unittest
from datetime import datetime,timezone
from scripts.measure_train.consistent_cut.subject import Subject,Refused
from scripts.measure_train.consistent_cut.epoch import EpochStamp
from scripts.measure_train.consistent_cut.observation import Observation
class T(unittest.TestCase):
 def test_scope(self):
  now=datetime.now(timezone.utc); e=EpochStamp(Subject("p/r","a"*40),1,"1"*64,now)
  o=Observation(Subject("c/r","b"*40),e,"REPOSITORY","PASS","e1",now)
  self.assertEqual(o.scope,"REPOSITORY")
  with self.assertRaises(Refused): Observation(o.consumer,e,"BAD","PASS","e2",now)
