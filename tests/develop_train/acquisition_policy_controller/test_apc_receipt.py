from dataclasses import replace
from scripts.develop_train.acquisition_policy_controller.subject import Subject
from scripts.develop_train.acquisition_policy_controller.receipt import issue,replay
S=Subject("seanchatmangpt/chatman-ecosystem","a"*40)
import unittest
class T(unittest.TestCase):
    def test_replay_and_tamper(self):
        r=issue(S,policy_generation=1,policy_digest="a"*64,frontier_digest="b"*64,selected_strategy="MAX_INFORMATION_GAIN",standing="PARTIAL_ALIVE")
        self.assertTrue(replay(r)); self.assertFalse(replay(replace(r,standing="ALIVE"))); self.assertFalse(replay(replace(r,actuation_performed=True)))
