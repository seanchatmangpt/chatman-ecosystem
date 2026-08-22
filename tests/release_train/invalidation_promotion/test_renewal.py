import unittest
from scripts.release_train.invalidation_promotion.subject import Subject, Refusal
from scripts.release_train.invalidation_promotion.binding import PromotionBinding
from scripts.release_train.invalidation_promotion.renewal import renew_binding
class T(unittest.TestCase):
 def test_schema_drift_refuses(self):
  a=Subject('x/a','a'*40); b=Subject('x/b','b'*40); bd=PromotionBinding(b,a,'c'*64,'v1','REPOSITORY','id')
  with self.assertRaises(Refusal): renew_binding(bd,schema='v2')
  self.assertEqual(renew_binding(bd,receipt='d'*64).receipt,'d'*64)
