import unittest
from datetime import datetime, timezone
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.epoch import EpochStamp
from scripts.release_train.coherent_epoch_promotion.cut import EvidenceCut
from scripts.release_train.coherent_epoch_promotion.dependency import DependencyGraph
from scripts.release_train.coherent_epoch_promotion.admission import admit_cut
class T(unittest.TestCase):
 def test_stale_epoch_refuses(self):
  t=datetime.now(timezone.utc); s=Subject.parse('o/r@'+'a'*40); e1=EpochStamp(s,1,'e1','b'*64,t); e2=EpochStamp(s,2,'e2','c'*64,t); g=DependencyGraph(); g.edges[s]=set()
  with self.assertRaisesRegex(ValueError,'STALE_CUT_EPOCH'): admit_cut(s,g,EvidenceCut(t,(e1,),()),{'o/r':e2})
