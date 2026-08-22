import unittest
from scripts.release_train.invalidation_promotion.subject import Subject, Refusal
from scripts.release_train.invalidation_promotion.binding import PromotionBinding
class T(unittest.TestCase):
 def test_binding_receipt(self):
  s=Subject('a/b','a'*40)
  self.assertEqual(PromotionBinding(s,s,'b'*64,'v1','REPOSITORY','id').schema,'v1')
  with self.assertRaises(Refusal): PromotionBinding(s,s,'bad','v1','REPOSITORY','id')
