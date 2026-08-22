import copy, unittest
from scripts.release_train.promotion_admission.receipt import *
class T(unittest.TestCase):
    def test_deterministic_tamper_sensitive(self):
        body={"standing":"PARTIAL_ALIVE","subjects":["x"],"actuation_performed":False}
        a=manufacture_receipt(body); b=manufacture_receipt(dict(body))
        self.assertEqual(a,b); self.assertTrue(replay_receipt(a))
        bad=copy.deepcopy(a); bad["body"]["standing"]="ALIVE"
        with self.assertRaisesRegex(ReceiptRefusal,"MISMATCH"): replay_receipt(bad)
if __name__=="__main__": unittest.main()
