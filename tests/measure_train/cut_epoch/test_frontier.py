import unittest
from datetime import datetime,timezone
from scripts.measure_train.cut_epoch.subject import Subject,Refused
from scripts.measure_train.cut_epoch.epoch import ProducerEpoch
from scripts.measure_train.cut_epoch.cut import EvidenceCut
from scripts.measure_train.cut_epoch.frontier import current_cut_frontier
class T(unittest.TestCase):
 def test_divergent_generation_refuses(self):
  now=datetime.now(timezone.utc); a=EvidenceCut(2,(ProducerEpoch(Subject("p/a","a"*40),2,"1"*64,now),)); b=EvidenceCut(2,(ProducerEpoch(Subject("p/b","b"*40),2,"2"*64,now),))
  with self.assertRaises(Refused): current_cut_frontier((a,b))
