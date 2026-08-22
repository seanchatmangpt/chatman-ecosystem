import unittest
from scripts.develop_train.regime_ensemble.sample import ErrorSample
from scripts.develop_train.regime_ensemble.cusum import detect as c
from scripts.develop_train.regime_ensemble.page_hinkley import detect as p
from scripts.develop_train.regime_ensemble.ewma import detect as e

class TestDetectors(unittest.TestCase):
    def test_shift_is_seen_by_independent_algorithms(self):
        xs=tuple(ErrorSample(i,v,"d") for i,v in enumerate([.1,.1,.2,.9,.9,.9,.9]))
        self.assertTrue(c(xs,.2,.05,.8).changed)
        self.assertTrue(p(xs,.02,.45).changed)
        self.assertTrue(e(xs,.2,.4,.35).changed)
if __name__ == "__main__": unittest.main()
