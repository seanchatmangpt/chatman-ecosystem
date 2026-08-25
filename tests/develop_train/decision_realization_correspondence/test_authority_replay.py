import unittest

from scripts.develop_train.decision_realization_correspondence import ActionClass, Receipt, Refused, replay
from scripts.develop_train.decision_realization_correspondence.authority import admit


class AuthorityReplayCourt(unittest.TestCase):
    def test_direct_do_refuses_and_replay_is_exact(self):
        with self.assertRaises(Refused):
            admit(ActionClass.DO)
        receipt = Receipt(
            "seanchatmangpt/chatman-ecosystem@" + "a" * 40,
            4,
            "PARTIAL_ALIVE",
            "b" * 64,
        )
        digest = receipt.digest()
        self.assertEqual(replay(receipt, digest), "REPLAY_MATCH")
        with self.assertRaises(Refused):
            replay(receipt, "0" * 64)


if __name__ == "__main__":
    unittest.main()
