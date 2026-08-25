from scripts.develop_train.process_convergence_substrate import *
import unittest

class TestAuthorityReceipt(unittest.TestCase):
    def test_do_refuses_and_receipt_tamper_refuses(self):
        self.assertEqual(admit_action(ActionClass.CONSTRUCT),ActionClass.CONSTRUCT)
        with self.assertRaises(Refused): admit_action(ActionClass.DO)
        r=Receipt("seanchatmangpt/chatman-ecosystem@"+"a"*40,3,"POTENTIAL","CONVERGING","PARTIAL_ALIVE")
        d=r.digest(); self.assertTrue(replay(r,d))
        with self.assertRaises(Refused): replay(r,"0"*64)
        with self.assertRaises(Refused): Receipt(r.subject,3,"POTENTIAL","CONVERGING","ALIVE",True)
