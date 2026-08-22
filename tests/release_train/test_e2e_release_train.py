import unittest
from scripts.release_train.train import manufacture_train
from scripts.release_train.receipt import replay

class EndToEndTests(unittest.TestCase):
    def test_multi_repo_delta_selects_dependency_closed_candidate_without_do(self):
        spec={
          "since":"2026-08-22T03:39:22Z","until":"2026-08-22T05:39:22Z",
          "evidence":[
            {"key":"gymact-pr65","repo":"seanchatmangpt/gymact","sha":"3"*40,"observed_at":"2026-08-22T04:30:00Z","status":"success","source":"github-pr"},
            {"key":"ceco-pr80","repo":"seanchatmangpt/chatman-ecosystem","sha":"2"*40,"observed_at":"2026-08-22T04:31:00Z","status":"in_progress","source":"github-pr"}],
          "dependencies":[{"upstream":"seanchatmangpt/gymact","downstream":"seanchatmangpt/chatman-ecosystem"}],
          "candidates":[
            {"key":"GYM","repo":"seanchatmangpt/gymact","value":7,"reversibility":9,"evidence":8,"release_criticality":7},
            {"key":"TRAIN","repo":"seanchatmangpt/chatman-ecosystem","value":10,"reversibility":10,"evidence":9,"release_criticality":10}],
          "actions":[{"kind":"SELECT","target":"TRAIN"},{"kind":"CONSTRUCT","target":"purpose-branch"},{"kind":"VERIFY","target":"exact-head"}],
          "gates":[{"name":"narrow","status":"success"},{"name":"compile","status":"success"}]
        }
        doc=manufacture_train(spec)
        self.assertEqual(doc["selected_candidate"]["key"],"TRAIN")
        self.assertEqual(doc["dependency_closure"],["seanchatmangpt/gymact","seanchatmangpt/chatman-ecosystem"])
        self.assertEqual(doc["observation_standing"],"UNKNOWN")
        self.assertEqual(doc["verification_standing"],"PARTIAL_ALIVE")
        self.assertTrue(replay(doc))
