import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.cut_strategy_runtime.cut import EvidenceCut
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.identity import Subject
from scripts.develop_train.cut_strategy_runtime.strategy import CutStrategy, select_cut
class StrategyCourt(unittest.TestCase):
    def cut(self, cid, cg, gens):
        now=datetime.now(timezone.utc); epochs=tuple(ProducerEpoch(Subject(f'acme/r{i}@'+chr(97+i)*40),g,chr(100+i)*64,now) for i,g in enumerate(gens))
        return EvidenceCut(cid,cg,epochs,now-timedelta(minutes=1),now+timedelta(hours=1))
    def test_strategies_can_choose_differently(self):
        newest=self.cut('newest',9,(2,2)); freshest=self.cut('freshest',8,(5,5))
        self.assertEqual(select_cut((newest,freshest),CutStrategy.LATEST_COMPLETE).cut_id,'newest')
        self.assertEqual(select_cut((newest,freshest),CutStrategy.MAX_FRESHNESS).cut_id,'freshest')
if __name__ == '__main__': unittest.main()
