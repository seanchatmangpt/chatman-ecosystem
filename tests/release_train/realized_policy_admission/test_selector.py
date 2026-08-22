import unittest
from scripts.release_train.realized_policy_admission.selector import Score,score,select
class T(unittest.TestCase):
    def test_preserves_differential(self):
        m=dict(lower_utility=.5,realized_gain=.8,cost_ratio=2,expected_entropy=.3)
        vals={s:score(s,**m) for s in ("MAX_INFORMATION_GAIN","MAX_INFORMATION_PER_COST","MIN_EXPECTED_ENTROPY")}
        self.assertEqual(len(set(vals.values())),3)
        self.assertEqual(select([Score("b",1,3),Score("a",1,4)]).strategy,"a")
