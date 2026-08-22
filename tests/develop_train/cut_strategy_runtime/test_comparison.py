import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.cut_strategy_runtime.comparison import pareto_frontier
from scripts.develop_train.cut_strategy_runtime.cut import EvidenceCut
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.identity import Subject
class ComparisonCourt(unittest.TestCase):
    def mk(self,cid,cg,gens):
        now=datetime.now(timezone.utc); eps=tuple(ProducerEpoch(Subject(f'acme/r{i}@'+chr(97+i)*40),g,chr(100+i)*64,now) for i,g in enumerate(gens))
        return EvidenceCut(cid,cg,eps,now-timedelta(minutes=1),now+timedelta(hours=1))
    def test_pareto_preserves_non_dominated_alternatives(self):
        cuts=(self.mk('latest',9,(2,2)), self.mk('fresh',8,(5,5)), self.mk('weak',1,(1,1)))
        self.assertEqual(pareto_frontier(cuts), ('fresh','latest'))
if __name__ == '__main__': unittest.main()
