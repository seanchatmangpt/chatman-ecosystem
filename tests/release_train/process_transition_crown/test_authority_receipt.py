import unittest
from scripts.release_train.process_transition_crown import SubjectEpoch, DependencyGraph, State, ActionClass, admit_action, Receipt, replay
from scripts.release_train.process_transition_crown.refusal import Refused

class AuthorityReceiptTest(unittest.TestCase):
    def test_transitive_blocker(self):
        g=DependencyGraph({"crown":("runtime",),"runtime":("tls",)})
        blockers=g.blockers("crown",{"tls":State.BUILD_BROKEN})
        self.assertEqual(blockers,("tls",))
    def test_direct_do_refuses(self):
        with self.assertRaises(Refused): admit_action(ActionClass.DO)
    def test_receipt_replay_and_tamper_boundary(self):
        s=SubjectEpoch("x/y","a"*40,1,"sem")
        leaf=Receipt(s,"leaf",(),{"ok":True})
        root=Receipt(s,"root",(leaf.digest(),),{"standing":"PARTIAL_ALIVE"})
        self.assertEqual(replay((leaf,root),root.digest()),root.digest())
        with self.assertRaises(Refused): Receipt(s,"bad",(),{},True).digest()

if __name__=="__main__": unittest.main()
