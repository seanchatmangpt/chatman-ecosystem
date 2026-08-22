import unittest
from dataclasses import replace
from scripts.develop_train.cut_strategy_runtime.authority import ActionClass, require_nonconsequential
from scripts.develop_train.cut_strategy_runtime.identity import Refusal
from scripts.develop_train.cut_strategy_runtime.persistence import StoreKind
from scripts.develop_train.cut_strategy_runtime.receipt import issue_receipt, replay_receipt
from scripts.develop_train.cut_strategy_runtime.strategy import CutStrategy
class ReceiptAuthorityCourt(unittest.TestCase):
    def test_receipt_is_tamper_sensitive_and_not_authority(self):
        r=issue_receipt(consumer='acme/app@'+'a'*40,selected_cut='c',strategy=CutStrategy.MIN_SKEW,store=StoreKind.JSONL,standing='PARTIAL_ALIVE',frontier=('c',),actuation_performed=False)
        self.assertTrue(replay_receipt(r)); self.assertFalse(replay_receipt(replace(r,standing='ALIVE')))
        with self.assertRaisesRegex(Refusal,'BRCE_REQUIRED'):
            require_nonconsequential(ActionClass.DO)
if __name__ == '__main__': unittest.main()
