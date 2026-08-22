import unittest
from scripts.develop_train.recovery_transaction.subject import Refusal
from scripts.develop_train.recovery_transaction.reliability import FailureModel
from scripts.develop_train.recovery_transaction.authority import ActionClass, require

class T(unittest.TestCase):
    def test_failure_schedule_is_seed_replayable(self):
        first = FailureModel(7, 0.5, 5)
        second = FailureModel(7, 0.5, 5)
        self.assertEqual(first.schedule(), second.schedule())
        self.assertEqual(first.first_success_attempt(), second.first_success_attempt())
    def test_direct_do_refuses(self):
        require(ActionClass.SELECT)
        require(ActionClass.CONSTRUCT)
        require(ActionClass.VERIFY)
        with self.assertRaises(Refusal):
            require(ActionClass.DO)

if __name__ == "__main__":
    unittest.main()
