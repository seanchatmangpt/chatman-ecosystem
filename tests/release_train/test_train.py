import unittest
from scripts.release_train.train import manufacture_train
from scripts.release_train.receipt import replay

class TrainTests(unittest.TestCase):
    def test_o_to_o_star_plan_is_receipted_and_non_actuating(self):
        spec={
          "since":"2026-08-22T03:00:00Z","until":"2026-08-22T05:00:00Z",
          "evidence":[{"key":"run","repo":"o/r","sha":"a"*40,"observed_at":"2026-08-22T04:00:00Z","status":"success","source":"actions"}],
          "dependencies":[{"upstream":"gymact","downstream":"chatman-ecosystem"}],
          "candidates":[{"key":"C1","repo":"chatman-ecosystem","value":8,"reversibility":9,"evidence":9,"release_criticality":10}],
          "actions":[{"kind":"SELECT","target":"C1"},{"kind":"CONSTRUCT","target":"branch"},{"kind":"VERIFY","target":"tests"}],
          "gates":[{"name":"narrow","status":"success"}]
        }
        doc=manufacture_train(spec)
        self.assertTrue(replay(doc))
        self.assertEqual(doc["dependency_closure"],["gymact","chatman-ecosystem"])
        self.assertFalse(doc["receipt"]["actuation_performed"])
