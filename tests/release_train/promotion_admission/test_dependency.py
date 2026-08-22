import unittest
from scripts.release_train.promotion_admission.subject import Subject
from scripts.release_train.promotion_admission.dependency import *
class T(unittest.TestCase):
    def test_closure_and_cycle(self):
        a=Subject("o/a","a"*40); b=Subject("o/b","b"*40)
        g=DependencyGraph({a:frozenset({b})}); self.assertEqual(g.closure(frozenset({a})),(b,a))
        with self.assertRaisesRegex(DependencyRefusal,"INCOMPLETE"): g.assert_closed(frozenset({a}))
        c=DependencyGraph({a:frozenset({b}),b:frozenset({a})})
        with self.assertRaisesRegex(DependencyRefusal,"CYCLE"): c.closure(frozenset({a}))
if __name__=="__main__": unittest.main()
