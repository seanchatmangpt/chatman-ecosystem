import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.cut_strategy_runtime.admission import CutAdmission
from scripts.develop_train.cut_strategy_runtime.cut import EvidenceCut
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.identity import Refusal, Subject
class AdmissionCourt(unittest.TestCase):
    def test_stale_epoch_refuses(self):
        now=datetime.now(timezone.utc); old=Subject('acme/api@'+'a'*40); new=Subject('acme/api@'+'c'*40)
        cut=EvidenceCut('cut',3,(ProducerEpoch(old,3,'b'*64,now),),now-timedelta(minutes=1),now+timedelta(hours=1))
        live=(ProducerEpoch(new,4,'d'*64,now),)
        with self.assertRaisesRegex(Refusal, 'STALE_CUT_EPOCH'):
            CutAdmission(cut,live,now).admit()
if __name__ == '__main__': unittest.main()
