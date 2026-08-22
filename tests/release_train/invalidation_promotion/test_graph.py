import unittest
from scripts.release_train.invalidation_promotion.subject import Subject, Refusal
from scripts.release_train.invalidation_promotion.binding import PromotionBinding
from scripts.release_train.invalidation_promotion.graph import DependencyGraph
R='c'*64
def b(consumer,producer): return PromotionBinding(consumer,producer,R,'v1','REPOSITORY',consumer.sha[:4]+producer.sha[:4])
class T(unittest.TestCase):
 def test_transitive_and_cycle(self):
  a=Subject('x/a','a'*40); c=Subject('x/c','c'*40); d=Subject('x/d','d'*40)
  self.assertEqual(DependencyGraph([b(c,a),b(d,c)]).descendants(a.key),((c.key,1),(d.key,2)))
  with self.assertRaises(Refusal): DependencyGraph([b(c,a),b(a,c)])
