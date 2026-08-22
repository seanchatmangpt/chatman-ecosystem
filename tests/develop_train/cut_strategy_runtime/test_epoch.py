import unittest
from datetime import datetime, timezone
from scripts.develop_train.cut_strategy_runtime.epoch import ProducerEpoch
from scripts.develop_train.cut_strategy_runtime.identity import Refusal, Subject
class EpochCourt(unittest.TestCase):
    def test_generation_receipt_and_time_are_bounded(self):
        s=Subject('acme/api@'+'a'*40)
        ProducerEpoch(s, 2, 'b'*64, datetime.now(timezone.utc))
        with self.assertRaisesRegex(Refusal, 'INVALID_GENERATION'):
            ProducerEpoch(s, -1, 'b'*64, datetime.now(timezone.utc))
        with self.assertRaisesRegex(Refusal, 'INVALID_EPOCH_RECEIPT'):
            ProducerEpoch(s, 1, 'bad', datetime.now(timezone.utc))
if __name__ == '__main__': unittest.main()
