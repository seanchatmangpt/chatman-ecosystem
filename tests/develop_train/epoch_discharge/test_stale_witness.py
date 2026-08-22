import unittest
from datetime import datetime,timezone,timedelta
from scripts.develop_train.epoch_discharge.identity import Subject
from scripts.develop_train.epoch_discharge.epoch import InvalidationEpoch
from scripts.develop_train.epoch_discharge.witness import Witness,WitnessKind
from scripts.develop_train.epoch_discharge.admission import admit_witness
class T(unittest.TestCase):
 def test_stale_generation_refuses(self):
  now=datetime.now(timezone.utc)-timedelta(seconds=1); p=Subject("a/p@"+"a"*40); c=Subject("a/c@"+"b"*40); e=InvalidationEpoch(p,3,"e","c"*64,now)
  w=Witness(p,c,2,"e",WitnessKind.DELIVERY,"w","d"*64,now+timedelta(milliseconds=1))
  with self.assertRaisesRegex(ValueError,"STALE_INVALIDATION_EPOCH"): admit_witness(e,w,{})
