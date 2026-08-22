import unittest
from datetime import datetime, timedelta, timezone
from scripts.develop_train.cut_strategy_runtime.authority import ActionClass
from scripts.develop_train.cut_strategy_runtime.cut import EvidenceCut
from scripts.develop_train.cut_strategy_runtime.engine import qualify
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.identity import Refusal, Subject
from scripts.develop_train.cut_strategy_runtime.persistence import PersistenceNeed
from scripts.develop_train.cut_strategy_runtime.receipt import replay_receipt
from scripts.develop_train.cut_strategy_runtime.strategy import CutStrategy
class EngineE2E(unittest.TestCase):
    def test_current_cut_qualifies_then_refuses_after_producer_advance(self):
        now=datetime.now(timezone.utc); a=Subject('acme/api@'+'a'*40); b=Subject('acme/db@'+'b'*40)
        epochs=(ProducerEpoch(a,4,'c'*64,now),ProducerEpoch(b,4,'d'*64,now))
        cut=EvidenceCut('cut-4',4,epochs,now-timedelta(minutes=1),now+timedelta(hours=1))
        q=qualify(consumer=Subject('acme/release@'+'e'*40),candidate_cuts=(cut,),current_epochs=epochs,now=now,strategy=CutStrategy.MIN_SKEW,persistence=PersistenceNeed(durable=True))
        self.assertEqual(q.standing,'PARTIAL_ALIVE'); self.assertFalse(q.receipt.actuation_performed); self.assertTrue(replay_receipt(q.receipt))
        advanced=(ProducerEpoch(Subject('acme/api@'+'f'*40),5,'1'*64,now),epochs[1])
        with self.assertRaisesRegex(Refusal,'STALE_CUT_EPOCH'):
            qualify(consumer=Subject('acme/release@'+'e'*40),candidate_cuts=(cut,),current_epochs=advanced,now=now,strategy=CutStrategy.MIN_SKEW,persistence=PersistenceNeed(),action=ActionClass.CONSTRUCT)
if __name__ == '__main__': unittest.main()
