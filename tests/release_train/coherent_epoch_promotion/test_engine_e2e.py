import unittest
from datetime import datetime, timezone
from scripts.release_train.coherent_epoch_promotion.subject import Subject
from scripts.release_train.coherent_epoch_promotion.epoch import EpochStamp
from scripts.release_train.coherent_epoch_promotion.observation import Observation,Scope,Outcome
from scripts.release_train.coherent_epoch_promotion.dependency import DependencyGraph
from scripts.release_train.coherent_epoch_promotion.cut import EvidenceCut
from scripts.release_train.coherent_epoch_promotion.engine import qualify
class T(unittest.TestCase):
 def test_coherent_generation_cut(self):
  t=datetime.now(timezone.utc); root=Subject.parse('o/root@'+'a'*40); dep=Subject.parse('o/dep@'+'b'*40); g=DependencyGraph(); g.add(root,dep)
  er=EpochStamp(root,3,'er','c'*64,t); ed=EpochStamp(dep,7,'ed','d'*64,t)
  obs=(Observation(root,er,Scope.REPOSITORY,Outcome.PASS,'r',t),Observation(dep,ed,Scope.REPOSITORY,Outcome.PASS,'d',t))
  out=qualify(root,g,EvidenceCut(t,(er,ed),obs),{'o/root':er,'o/dep':ed},True)
  self.assertEqual(out['standing'],'PARTIAL_ALIVE'); self.assertEqual(out['persistence'],'SQLITE'); self.assertEqual(out['phases'],['VERIFY','CONSTRUCT']); self.assertFalse(out['actuation_performed'])
