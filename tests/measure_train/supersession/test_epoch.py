import unittest
from datetime import datetime, timezone
from scripts.measure_train.supersession.epoch import Epoch
from scripts.measure_train.supersession.subject import Refused

class TestEpoch(unittest.TestCase):
    def test_timezone_and_sequence(self):
        self.assertEqual(Epoch(datetime.now(timezone.utc), 0).sequence, 0)
        with self.assertRaises(Refused):
            Epoch(datetime.now(), 1)
