import unittest
from scripts.measure_train.process_intelligence_closure.powl import PowlModel
from scripts.measure_train.process_intelligence_closure.subject import Refused

class T(unittest.TestCase):
    def test_strict_order_acyclic_choice_bounded(self):
        model=PowlModel(("a","b"),(('a','b'),),(('a','b'),('b','a')),cycle_bound=3)
        self.assertEqual(model.dependencies(),(('a','b'),))
        with self.assertRaises(Refused): PowlModel(("a","b"),(('a','b'),('b','a')))
        with self.assertRaises(Refused): PowlModel(("a","b"),(),(('a','b'),),cycle_bound=0)
