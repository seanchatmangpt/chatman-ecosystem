import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.cut_strategy_runtime.cut import EvidenceCut
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.identity import Refusal, Subject
class CutCourt(unittest.TestCase):
    def test_duplicate_producer_refuses(self):
        now=datetime.now(timezone.utc); s=Subject('acme/api@'+'a'*40); e=ProducerEpoch(s,1,'b'*64,now)
        with self.assertRaisesRegex(Refusal, 'DUPLICATE_CUT_PRODUCER'):
            EvidenceCut('c',1,(e,e),now,now+timedelta(hours=1))
if __name__ == '__main__': unittest.main()
