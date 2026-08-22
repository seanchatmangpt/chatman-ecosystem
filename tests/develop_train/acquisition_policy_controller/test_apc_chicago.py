from datetime import datetime, timezone, timedelta
from scripts.develop_train.acquisition_policy_controller.subject import Subject,Refusal
from scripts.develop_train.acquisition_policy_controller.realization import Realization
from scripts.develop_train.acquisition_policy_controller.policy import Policy
from scripts.develop_train.acquisition_policy_controller.frontier import PolicyFrontier
from scripts.develop_train.acquisition_policy_controller.dependency import DependencyGraph
from scripts.develop_train.acquisition_policy_controller.controller import qualify
S=Subject("seanchatmangpt/chatman-ecosystem","a"*40); NOW=datetime.now(timezone.utc)-timedelta(seconds=1)
def row(strategy,gain,cid): return Realization(S,"p",cid,strategy,1,.2,gain,1,1,10,10,NOW,"PASS")
import unittest
class T(unittest.TestCase):
    def test_feedback_then_generation_move_refuses(self):
        pol=Policy(1,0,1,10,100,.5); f=PolicyFrontier(1,pol.digest,"e"*64); g=DependencyGraph({"root":()}, {})
        rows=[row("MAX_INFORMATION_GAIN",.6,"a"),row("MAX_INFORMATION_PER_COST",.2,"b"),row("MIN_EXPECTED_ENTROPY",.1,"c")]
        self.assertEqual(qualify(S,pol,rows,f,g,"root",1).selected_strategy,"MAX_INFORMATION_GAIN")
        with self.assertRaises(Refusal): qualify(S,pol,rows,f,g,"root",2)
