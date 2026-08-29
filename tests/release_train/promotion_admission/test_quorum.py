import unittest
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.admission import SubjectAdmission
from scripts.release_train.promotion_admission.quorum import evaluate_quorum
class T(unittest.TestCase):
    def test_dependency_blocker_prevents_quorum(self):
        a=Subject("o/a","a"*40); b=Subject("o/b","b"*40)
        q=evaluate_quorum((b,a),{b:SubjectAdmission(b,False,("x",)),a:SubjectAdmission(a,True,())})
        self.assertEqual(q.standing,"BLOCKED"); self.assertEqual(q.blocked,(b,))
if __name__=="__main__": unittest.main()
