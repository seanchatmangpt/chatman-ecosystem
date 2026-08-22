import unittest
from scripts.develop_train.cut_strategy_runtime.identity import Refusal, Subject
class IdentityCourt(unittest.TestCase):
    def test_exact_subject_required(self):
        good = Subject('acme/api@' + 'a'*40)
        self.assertEqual(good.repository, 'acme/api')
        with self.assertRaisesRegex(Refusal, 'INEXACT_SUBJECT'):
            Subject('acme/api@abc123')
if __name__ == '__main__': unittest.main()
