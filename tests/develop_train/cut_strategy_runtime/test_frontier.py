import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.cut_strategy_runtime.cut import EvidenceCut
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.frontier import CutFrontier
from scripts.develop_train.cut_strategy_runtime.identity import Subject
class FrontierCourt(unittest.TestCase):
    def test_only_latest_cut_generation_enters_selection(self):
        now=datetime.now(timezone.utc); e=ProducerEpoch(Subject('acme/api@'+'a'*40),1,'b'*64,now)
        old=EvidenceCut('old',1,(e,),now-timedelta(minutes=1),now+timedelta(hours=1)); new=EvidenceCut('new',2,(e,),now-timedelta(minutes=1),now+timedelta(hours=1))
        self.assertEqual(tuple(c.cut_id for c in CutFrontier((old,new)).current()), ('new',))
if __name__ == '__main__': unittest.main()
