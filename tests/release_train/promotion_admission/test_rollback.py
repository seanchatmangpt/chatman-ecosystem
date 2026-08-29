import unittest
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.rollback import *
class T(unittest.TestCase):
    def test_external_compensation_refuses(self):
        s=Subject("o/r","a"*40)
        RollbackBoundary("b"*40,(s,))
        with self.assertRaisesRegex(RollbackRefusal,"EXTERNAL_COMPENSATION"): RollbackBoundary("b"*40,(s,),True)
if __name__=="__main__": unittest.main()
