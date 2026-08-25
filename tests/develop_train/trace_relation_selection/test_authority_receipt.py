import unittest
from scripts.develop_train.trace_relation_selection import *

class TestAuthorityReceipt(unittest.TestCase):
    def test_do_and_tamper_refuse(self):
        with self.assertRaises(Refused):
            admit(ActionClass.DO)
        r=Receipt("repo/x@"+"a"*40+":"+"b"*64,1,("EXACT",),"PARTIAL_ALIVE")
        self.assertTrue(replay(r,r.digest))
        with self.assertRaises(Refused):
            replay(r,"0"*64)
        with self.assertRaises(Refused):
            Receipt("x",1,(),"UNKNOWN",actuation_performed=True)
