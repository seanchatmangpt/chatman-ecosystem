import unittest
from datetime import datetime, timezone, timedelta
from scripts.release_train.realized_policy_admission.realization import Realization
class T(unittest.TestCase):
    def test_utility_and_future_refusal(self):
        r=Realization("MAX_INFORMATION_GAIN",.4,.5,1,1,1,1,False,datetime.now(timezone.utc)-timedelta(seconds=1))
        self.assertAlmostEqual(r.utility,.5); self.assertAlmostEqual(r.residual,.1)
        with self.assertRaisesRegex(ValueError,"INVALID_REALIZATION_TIME"):
            Realization("MAX_INFORMATION_GAIN",.4,.5,1,1,1,1,False,datetime.now(timezone.utc)+timedelta(days=1))
